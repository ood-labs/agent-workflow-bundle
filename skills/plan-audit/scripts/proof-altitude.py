#!/usr/bin/env python3
"""Proof-altitude screen for a phase doc's pass criteria, judged by Jev (TypeSafe System One).

Usage:
    python proof-altitude.py <phase-doc.md> [--json] [--user-facing yes|no|auto]

Extracts every pass criterion it can find in the phase doc, sends one batched request
to the TypeSafe API, and prints a table with a verdict per criterion:

    REWRITE  a stub could clear it (mock >= 0.75) or it proves nothing visible/behavioral
             (altitude < 2) on a user-facing phase
    READ     Jev is unsure about the altitude (score confidence < 0.3); read it yourself
    OK       neither of the above

Jev judges; this script decides nothing beyond the verdict column, and /plan-audit's
acceptance-bar agent still owns the fix. Needs TYPESAFE_API_KEY in the environment.
Exit code is always 0; a missing key, network failure, or a doc with no criteria is
reported on stdout as `skipped: <reason>` so a calling skill can fall back to prose.
Standard library only.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

MOCK_THRESHOLD = 0.75      # mock_can_pass at or above this -> REWRITE
ALTITUDE_FLOOR = 2.0       # altitude below this on a user-facing phase -> REWRITE
CONFIDENCE_FLOOR = 0.30    # altitude confidence below this -> READ

ALTITUDE_LEVELS = [
    "artifact-exists: only checks that something was produced or a call returned",
    "readback: returned values match expectation, no visible or behavioral gate",
    "behavioral: the feature must execute and its output must change observably",
    "visible-asserted: a human-visible result with an assertion on what must be seen",
]

# Inline markers that introduce a criterion on the same line.
INLINE_MARKERS = re.compile(
    r"^\s*(?:[-*]\s+)?\*\*(verification|pass criteri(?:on|a)|definition of done|proof)\*\*\s*:?\s*(.+)$",
    re.IGNORECASE,
)
# Headings under which every bullet is a criterion.
SECTION_HEADINGS = re.compile(
    r"^#{1,6}\s*(success criteria|pass criteria|pass criterion|verification plan|verification|acceptance criteria|definition of done)\b",
    re.IGNORECASE,
)
ANY_HEADING = re.compile(r"^#{1,6}\s")
BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(?:\[[ xX]\]\s*)?(.+)$")
SUBPHASE_HEADING = re.compile(r"^#{2,4}\s*(\S+):\s*(.+)$")


def extract_criteria(text):
    """Return an ordered list of (id, criterion_text, context_heading)."""
    found = []
    in_section = False
    current_heading = ""
    seen = set()

    def add(crit, heading):
        crit = crit.strip().rstrip(".")
        if len(crit) < 8 or crit in seen:
            return
        seen.add(crit)
        found.append((f"c{len(found) + 1}", crit, heading))

    for line in text.splitlines():
        if ANY_HEADING.match(line):
            in_section = bool(SECTION_HEADINGS.match(line))
            m = SUBPHASE_HEADING.match(line)
            current_heading = line.lstrip("# ").strip() if not m else f"{m.group(1)}: {m.group(2)}"
            continue
        m = INLINE_MARKERS.match(line)
        if m:
            add(m.group(2), current_heading)
            continue
        if in_section:
            b = BULLET.match(line)
            if b:
                add(b.group(1), current_heading)
    return found


def extract_overview(text, limit=900):
    """First paragraph after a Goal/Overview heading, else the first body paragraph."""
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if re.match(r"^#{1,3}\s*(goal|overview)\b", line, re.IGNORECASE):
            start = i + 1
            break
    para = []
    for line in lines[start:]:
        if line.startswith("#") and para:
            break
        if line.strip():
            para.append(line.strip())
        elif para:
            break
    return " ".join(para)[:limit]


def build_questions(criteria, user_facing):
    qs = {}
    uf = (
        "The phase is user-facing: a human is meant to see or do something."
        if user_facing == "yes"
        else "The phase is substrate only; nothing user-visible is promised."
        if user_facing == "no"
        else "Decide from `phase_context` whether a human is meant to see or do something."
    )
    for cid, _, _ in criteria:
        qs[f"mock_{cid}"] = {
            "type": "noul",
            "instructions": (
                f"Could a stubbed, placeholder, or model-only build pass pass criterion "
                f"`criteria.{cid}.text` (from sub-phase `criteria.{cid}.context`) without the real feature existing? {uf}"
            ),
            "criteria": {
                "true": (
                    "Only a proxy layer is checked: a readback returns expected JSON, a log line appears, "
                    "a file or capture exists, a tool call returns without error. Canned data would clear it."
                ),
                "false": (
                    "False unless the real experience exists: a human sees specific content, an action "
                    "produces an observable change, execution output changes, or an assertion on capture "
                    "content (vision_eval style) is required."
                ),
            },
        }
        qs[f"alt_{cid}"] = {
            "type": "score",
            "instructions": f"Rate the proof altitude of pass criterion `criteria.{cid}.text`.",
            "criteria": ALTITUDE_LEVELS,
        }
    return qs


def call_api(key, state, questions, timeout=90):
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def verdict(mock, altitude, confidence, user_facing):
    if confidence < CONFIDENCE_FLOOR:
        return "READ"
    if mock >= MOCK_THRESHOLD:
        return "REWRITE"
    if user_facing != "no" and altitude < ALTITUDE_FLOOR:
        return "REWRITE"
    return "OK"


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = argv[0]
    as_json = "--json" in argv
    user_facing = "auto"
    if "--user-facing" in argv:
        i = argv.index("--user-facing")
        if i + 1 < len(argv) and argv[i + 1] in ("yes", "no", "auto"):
            user_facing = argv[i + 1]

    def skip(reason):
        if as_json:
            print(json.dumps({"skipped": reason, "doc": path}))
        else:
            print(f"skipped: {reason}")
        return 0

    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return skip("TYPESAFE_API_KEY not set")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return skip(f"cannot read {path}: {e}")

    criteria = extract_criteria(text)
    if not criteria:
        return skip("no pass criteria found (looked for **Verification**/**Pass criterion** lines and bullets under Success/Pass/Acceptance Criteria or Verification Plan headings)")

    state = {
        "phase_context": extract_overview(text),
        "criteria": {cid: {"text": t, "context": h} for cid, t, h in criteria},
    }
    try:
        resp = call_api(key, state, build_questions(criteria, user_facing))
    except urllib.error.HTTPError as e:
        return skip(f"API HTTP {e.code}: {e.read()[:200].decode(errors='replace')}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return skip(f"API unreachable: {e}")

    answers = resp.get("answers", {})
    rows = []
    for cid, t, h in criteria:
        m = answers.get(f"mock_{cid}", {})
        a = answers.get(f"alt_{cid}", {})
        mock = float(m.get("noul", 0.0))
        alt = float(a.get("score", 0.0))
        conf = float(a.get("confidence", 0.0))
        rows.append({
            "id": cid, "context": h, "text": t,
            "mock_can_pass": round(mock, 2), "altitude": round(alt, 2),
            "confidence": round(conf, 2), "verdict": verdict(mock, alt, conf, user_facing),
        })

    usage = resp.get("usage", {})
    if as_json:
        print(json.dumps({"doc": path, "model": resp.get("model", MODEL), "usage": usage, "rows": rows}, indent=2))
        return 0

    print(f"Proof-altitude screen: {path}")
    print(f"model={resp.get('model', MODEL)} input_tokens={usage.get('input_tokens', '?')} "
          f"criteria={len(rows)} user_facing={user_facing}")
    print(f"policy: REWRITE if mock>={MOCK_THRESHOLD} or altitude<{ALTITUDE_FLOOR} (user-facing); READ if conf<{CONFIDENCE_FLOOR}")
    print()
    print(f"{'id':4} {'verdict':8} {'mock':>5} {'alt':>5} {'conf':>5}  criterion")
    for r in rows:
        ctx = f"[{r['context']}] " if r["context"] else ""
        print(f"{r['id']:4} {r['verdict']:8} {r['mock_can_pass']:5.2f} {r['altitude']:5.2f} {r['confidence']:5.2f}  {ctx}{r['text']}")
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print()
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
