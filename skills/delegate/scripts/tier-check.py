#!/usr/bin/env python3
"""Prove which model each delegated agent ran on, from the runner's own transcripts.

  python tier-check.py --runner claude --since 2026-09-22T10:00:00 \
      --expect scout=claude-sonnet- --expect worker=claude-sonnet- --main claude-fable-
  python tier-check.py --runner codex  --since 2026-09-22T10:00:00 \
      --expect scout=gpt-6-luna --expect worker=gpt-6-luna --main gpt-6-astra

Exit 0 only when every expected role has a transcript newer than --since whose every
model string starts with the expected prefix, and the main/parent model starts with
--main. Otherwise exit 1 and print one FAIL line per problem, naming the model seen.
Missing evidence is a FAIL, never a pass.

Roles are identified by a `ROLE:<name>` marker in the agent's first user message;
the /tier-check skill puts that marker in every prompt it dispatches.
Standard library only.
"""

import argparse
import datetime as dt
import json
import os
import re
import sys

ROLE_RE = re.compile(r"ROLE:([a-z][a-z0-9_-]*)")


def parse_since(s):
    if s is None:
        return 0.0
    try:
        return dt.datetime.fromisoformat(s).timestamp()
    except (OSError, OverflowError, ValueError):
        return 0.0


def iter_jsonl(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(str(c.get("text", "")))
                if c.get("type") == "tool_use":
                    parts.append(json.dumps(c.get("input", {})))
        return " ".join(parts)
    return ""


def _find_role(text):
    m = ROLE_RE.search(text)
    return m.group(1) if m else None


def scan_claude(projects_dir, project_key, since_ts):
    projects_dir = str(projects_dir)
    root = os.path.join(projects_dir, project_key)
    out = {"main": [], "agents": {}}
    if not os.path.isdir(root):
        return out
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if name.endswith(".jsonl") and os.path.isfile(path) and os.path.getmtime(path) >= since_ts:
            for row in iter_jsonl(path):
                if row.get("type") == "assistant" and not row.get("isSidechain"):
                    model = (row.get("message") or {}).get("model")
                    if model and model != "<synthetic>":
                        out["main"].append(model)
        sub = os.path.join(path, "subagents")
        if os.path.isdir(sub):
            for f in sorted(os.listdir(sub)):
                fp = os.path.join(sub, f)
                if not f.endswith(".jsonl") or os.path.getmtime(fp) < since_ts:
                    continue
                role, models = None, []
                for row in iter_jsonl(fp):
                    msg = row.get("message") or {}
                    if role is None and row.get("type") == "user":
                        role = _find_role(_text_of(msg.get("content")))
                    if row.get("type") == "assistant":
                        model = msg.get("model")
                        if model and model != "<synthetic>":
                            models.append(model)
                if role and models:
                    out["agents"].setdefault(role, []).extend(sorted(set(models)))
    return out


def scan_codex(sessions_dir, since_ts):
    out = {"main": [], "agents": {}}
    for dirpath, _, files in os.walk(str(sessions_dir)):
        for f in files:
            fp = os.path.join(dirpath, f)
            if not f.endswith(".jsonl") or os.path.getmtime(fp) < since_ts:
                continue
            models, role, spawns = [], None, False
            for row in iter_jsonl(fp):
                payload = row.get("payload") or {}
                if row.get("type") == "event_msg" and payload.get("type") == "thread_settings_applied":
                    model = (payload.get("thread_settings") or {}).get("model")
                    if model:
                        models.append(model)
                if payload.get("type") == "message":
                    text = _text_of(payload.get("content"))
                    r = _find_role(text)
                    if r and role is None and payload.get("role") == "user" and not text.lower().startswith("spawn"):
                        role = r
                    if r and text.lower().startswith("spawn"):
                        spawns = True
            if not models:
                continue
            if role and not spawns:
                out["agents"].setdefault(role, []).extend(sorted(set(models)))
            else:
                out["main"].extend(sorted(set(models)))
    return out


def evaluate(scan, expects, main_prefix):
    problems = []
    for role, prefix in expects.items():
        seen = scan["agents"].get(role)
        if not seen:
            problems.append(f"FAIL {role}: no transcript newer than --since carries ROLE:{role}")
            continue
        bad = [m for m in seen if not m.startswith(prefix)]
        if bad:
            problems.append(f"FAIL {role}: expected model prefix '{prefix}', saw {sorted(set(bad))}")
    if main_prefix:
        mains = scan["main"]
        if not mains:
            problems.append("FAIL main: no main-session model found in transcripts newer than --since")
        else:
            bad = [m for m in mains if not m.startswith(main_prefix)]
            if bad:
                problems.append(f"FAIL main: expected prefix '{main_prefix}', saw {sorted(set(bad))}")
    return (not problems), problems


def default_project_key(cwd):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runner", choices=["claude", "codex"], required=True)
    ap.add_argument("--since", help="ISO-8601 local time; only transcripts modified at/after this count")
    ap.add_argument("--expect", action="append", default=[], help="ROLE=MODEL_PREFIX, repeatable")
    ap.add_argument("--main", default="", help="expected model prefix of the main/parent session")
    ap.add_argument("--claude-projects-dir", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--project-key", default=None)
    ap.add_argument("--codex-sessions-dir", default=os.path.expanduser("~/.codex/sessions"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    expects = {}
    for e in a.expect:
        role, _, prefix = e.partition("=")
        if not role or not prefix:
            ap.error(f"--expect needs ROLE=PREFIX, got {e!r}")
        expects[role] = prefix
    since_ts = parse_since(a.since)

    if a.runner == "claude":
        key = a.project_key or default_project_key(os.getcwd())
        scan = scan_claude(a.claude_projects_dir, key, since_ts)
    else:
        scan = scan_codex(a.codex_sessions_dir, since_ts)

    ok, problems = evaluate(scan, expects, a.main)
    if a.json:
        print(json.dumps({"ok": ok, "problems": problems, "scan": scan}, indent=2))
    else:
        for role, models in sorted(scan["agents"].items()):
            print(f"  {role:8} ran on {sorted(set(models))}")
        print(f"  {'main':8} ran on {sorted(set(scan['main']))}")
        for p in problems:
            print(p)
        print("PASS: every role ran on its expected tier" if ok else f"RESULT: {len(problems)} problem(s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
