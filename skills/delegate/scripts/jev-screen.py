#!/usr/bin/env python3
"""Jev screens for the delegate doctrine: order and gate what the judge reads.

    python jev-screen.py finding-triage < findings.json
    python jev-screen.py diff-risk      < diff.json

finding-triage input : {"doctrine": "...", "findings": [{"id","agent","claim","proposed_change","citation"}]}
finding-triage output: {"usage", "rows": [{"id","bucket","bucket_confidence","safe_to_auto_apply","verdict"}]}
                       verdict: AUTO_APPLY | REVIEW | ASK
diff-risk input      : {"slice": {"id","pass_criterion","allowed_files"}, "hunks": [{"id","file","summary"}]}
diff-risk output     : {"usage", "slice_status", "slice_confidence", "rows": [{"id","file","needs_close_review","order"}]}

Jev judges; the judge (the session) still reads everything and owns every edit.
Always exits 0. Any environmental failure prints {"skipped": "<reason>"}.
Needs TYPESAFE_API_KEY. Standard library only.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

SAFE_FLOOR = 0.80
BUCKET_CONF_FLOOR = 0.60


def _num(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


BUCKETS = {
    "derived_fix": "Mechanical and unambiguous: missing pass criterion, unnamed dependency, dangling citation, wrong version corrected with evidence, a small safe code fix",
    "judgement_call": "Resolving it requires a choice on the user's behalf: dropping a deliverable, picking a replacement library, adding a sub-phase, restructuring, a design decision",
    "unresolvable": "No defensible best guess exists from spec, research, conversation, or codebase",
    "not_a_finding": "Reviewed and fine as is; no change needed",
    "unclear": "The finding text does not carry enough to decide",
}


def build_questions(mode, doc):
    qs = {}
    if mode == "finding-triage":
        for i, f in enumerate(doc.get("findings", [])):
            fid = f["id"]
            qs[f"bucket_{fid}"] = {
                "type": "choice",
                "instructions": f"Sort audit finding `findings[{i}]` into the bucket the skill should use, per the apply-now doctrine in `doctrine`.",
                "criteria": dict(BUCKETS),
            }
            qs[f"safe_{fid}"] = {
                "type": "noul",
                "instructions": f"Is applying `findings[{i}].proposed_change` without asking the user consistent with `doctrine`?",
                "criteria": {
                    "true": "Small, mechanical, adds no architecture, requires no design decision the user has not made, rests on a verified citation",
                    "false": "Expands scope, picks between designs, touches something irreversible, or rests on an unverified claim",
                },
            }
    elif mode == "diff-risk":
        for i, h in enumerate(doc.get("hunks", [])):
            qs[f"risk_{h['id']}"] = {
                "type": "noul",
                "instructions": f"Does hunk `hunks[{i}]` need the judge's close, line-by-line review before it can be committed toward `slice.pass_criterion`?",
                "criteria": {
                    "true": "Touches control flow, error handling, security, concurrency, persistence, a public interface, or a file not in `slice.allowed_files`; or its summary does not obviously serve the pass criterion",
                    "false": "Rename, comment, formatting, test fixture, or a local change whose summary plainly serves the pass criterion",
                },
            }
        qs["slice_status"] = {
            "type": "choice",
            "instructions": "Taking all `hunks` together, what is the state of sub-slice `slice` against `slice.pass_criterion`?",
            "criteria": {
                "meets_criterion": "The hunks, if correct, would satisfy the pass criterion in full",
                "partial": "Progress toward the criterion but something it requires is missing",
                "off_scope": "Work outside the slice's files or criterion dominates",
                "unclear": "Cannot tell from the hunk summaries",
            },
        }
    else:
        raise ValueError(f"unknown mode {mode}")
    return qs


def decide_finding(bucket, bucket_conf, safe):
    if bucket in ("unresolvable", "unclear"):
        return "ASK"
    if bucket == "derived_fix" and bucket_conf >= BUCKET_CONF_FLOOR and safe >= SAFE_FLOOR:
        return "AUTO_APPLY"
    return "REVIEW"


def decide_diff(answers, hunks):
    rows = []
    for h in hunks:
        a = answers.get(f"risk_{h['id']}", {})
        rows.append({"id": h["id"], "file": h.get("file", ""), "needs_close_review": round(_num(a.get("noul"), 1.0), 2)})
    for order, r in enumerate(sorted(rows, key=lambda r: -r["needs_close_review"]), start=1):
        r["order"] = order
    s = answers.get("slice_status", {})
    return {"slice_status": s.get("choice", "unclear"), "slice_confidence": round(_num(s.get("confidence"), 0.0), 2), "rows": rows}


def call_api(key, state, questions, timeout=90):
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(API_URL, data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def run(mode, doc):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return {"skipped": "TYPESAFE_API_KEY not set"}
    try:
        questions = build_questions(mode, doc)
    except (KeyError, ValueError, TypeError) as e:
        return {"skipped": f"bad input: {e}"}
    if not questions:
        return {"skipped": "nothing to screen"}
    try:
        resp = call_api(key, doc, questions)
    except urllib.error.HTTPError as e:
        return {"skipped": f"API HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"skipped": f"API unreachable: {e}"}
    try:
        answers = resp.get("answers", {})
        out = {"usage": resp.get("usage", {})}
        if mode == "finding-triage":
            rows = []
            for f in doc.get("findings", []):
                b = answers.get(f"bucket_{f['id']}", {})
                s = answers.get(f"safe_{f['id']}", {})
                bucket = b.get("choice", "unclear")
                conf = _num(b.get("confidence"), 0.0)
                safe = _num(s.get("noul"), 0.0)
                rows.append({"id": f["id"], "bucket": bucket, "bucket_confidence": round(conf, 2),
                             "safe_to_auto_apply": round(safe, 2), "verdict": decide_finding(bucket, conf, safe)})
            out["rows"] = rows
        else:
            out.update(decide_diff(answers, doc.get("hunks", [])))
    except (KeyError, ValueError, TypeError) as e:
        return {"skipped": f"bad response or input: {e}"}
    return out


def main(argv):
    try:
        sys.stdin.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if not argv:
        print(__doc__)
        return 0
    if argv[0] not in ("finding-triage", "diff-risk"):
        print(json.dumps({"skipped": f"unknown mode {argv[0]!r}; use finding-triage or diff-risk"}))
        return 0
    try:
        doc = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(json.dumps({"skipped": f"bad input: {e}"}))
        return 0
    print(json.dumps(run(argv[0], doc), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
