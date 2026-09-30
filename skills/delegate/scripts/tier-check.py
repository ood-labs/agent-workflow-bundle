#!/usr/bin/env python3
"""Prove which model each delegated agent ran on, from the runner's own transcripts.
At least one --expect and a non-empty --main are required; running with nothing to
verify is a failure, not a pass.

  python tier-check.py --runner claude --since 2026-09-22T10:00:00 \
      --expect scout=claude-sonnet- --expect worker=claude-sonnet- --main claude-fable-
  python tier-check.py --runner codex  --since 2026-09-22T10:00:00 \
      --expect scout=gpt-6-luna --expect worker=gpt-6-luna --main gpt-6-astra

Exit 0 only when every expected role has a transcript newer than --since whose every
model string starts with the expected prefix, and the main/parent model starts with
--main. Otherwise exit 1 and print one FAIL line per problem, naming the model seen.
Missing evidence is a FAIL, never a pass.

Roles are identified by the runner's own record where it has one (Codex multi_agent
v2: `session_meta.agent_role` of the spawned thread's file), otherwise by a
`ROLE:<name>` marker in the agent's first user message; the /tier-check skill puts
that marker in every prompt it dispatches.
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
    """Parse --since as a naive local ISO-8601 timestamp into a UTC epoch float.

    None (no --since given) returns 0.0: include everything. A string that does not
    parse as ISO-8601 is a user error, not a silent fallback: raise
    argparse.ArgumentTypeError so argparse reports it against --since and exits 2.
    A string that parses but whose .timestamp() conversion itself fails (e.g. a
    pre-1970 local time on Windows) falls back to 0.0 rather than crashing.
    """
    if s is None:
        return 0.0
    try:
        parsed = dt.datetime.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid ISO-8601 timestamp: {s!r}")
    try:
        return parsed.timestamp()
    except (OSError, OverflowError, ValueError):
        return 0.0


def _row_ts(row):
    """Parse a transcript row's `timestamp` field (ISO-8601, typically Z-suffixed UTC)
    into a UTC epoch float. Returns None when the field is missing or unparsable;
    callers treat None as "always include" so timestamp-less rows are never wrongly
    excluded by --since.
    """
    ts = row.get("timestamp")
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return None


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
                    row_ts = _row_ts(row)
                    if row_ts is not None and row_ts < since_ts:
                        continue
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
                        row_ts = _row_ts(row)
                        if row_ts is not None and row_ts < since_ts:
                            continue
                        model = msg.get("model")
                        if model and model != "<synthetic>":
                            models.append(model)
                if role and models:
                    out["agents"].setdefault(role, []).extend(sorted(set(models)))
    return out


def _codex_session_meta(fp):
    for row in iter_jsonl(fp):
        if row.get("type") == "session_meta":
            return row.get("payload") or {}
    return None


def _scan_codex_threaded(fp, meta, since_ts, out):
    """multi_agent v2 rollouts (verified on a real Codex run, 2026-09-29): every thread
    is its own file. A spawned agent's `session_meta` carries `thread_source: subagent`
    and `agent_role` (the installed definition's name, e.g. scout); the parent carries
    `thread_source: user`. The model a thread ran on is `turn_context.payload.model`.
    `session_meta.base_instructions.provenance.model` names the PARENT's model even in
    a child file, so it is never read as evidence.
    """
    source = meta.get("source")  # a plain string ("vscode", "cli") on a user thread
    subagent = source.get("subagent") if isinstance(source, dict) else None
    spawn = (subagent.get("thread_spawn") if isinstance(subagent, dict) else None) or {}
    role = meta.get("agent_role") or spawn.get("agent_role")
    is_child = meta.get("thread_source") == "subagent" or bool(spawn)
    models, marker = [], None
    for row in iter_jsonl(fp):
        payload = row.get("payload") or {}
        if row.get("type") == "turn_context":
            row_ts = _row_ts(row)
            if row_ts is not None and row_ts < since_ts:
                continue
            if payload.get("model"):
                models.append(payload["model"])
        elif marker is None and payload.get("type") == "message" and payload.get("role") == "user":
            marker = _find_role(_text_of(payload.get("content")))
    if not models:
        return
    if is_child:
        role = role or marker
        if role:
            out["agents"].setdefault(role, []).extend(sorted(set(models)))
        else:
            for m in models:
                if m not in out["codex_spawned_models"]:
                    out["codex_spawned_models"].append(m)
    else:
        out["main"].extend(sorted(set(models)))


def scan_codex(sessions_dir, since_ts):
    """Scan Codex rollout JSONL files.

    Two shapes. Current Codex (multi_agent v2) writes one file per thread and names the
    role in `session_meta`; see _scan_codex_threaded. An older shape kept every thread
    in ONE file, a spawned thread showing up as an additional `thread_settings_applied`
    row; there the first model is the parent's and every later one that differs is a
    spawned-thread model, recorded under `codex_spawned_models` so a FAIL can name what
    it saw, and roles come only from a ROLE: marker, which that shape rarely carries.
    """
    out = {"main": [], "agents": {}, "codex_spawned_models": []}
    for dirpath, _, files in os.walk(str(sessions_dir)):
        for f in files:
            fp = os.path.join(dirpath, f)
            if not f.endswith(".jsonl") or os.path.getmtime(fp) < since_ts:
                continue
            meta = _codex_session_meta(fp)
            if meta is not None and "thread_source" in meta:
                _scan_codex_threaded(fp, meta, since_ts, out)
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
            main_model = models[0]
            for m in models[1:]:
                if m != main_model and m not in out["codex_spawned_models"]:
                    out["codex_spawned_models"].append(m)
            if role and not spawns:
                out["agents"].setdefault(role, []).extend(sorted(set(models)))
            else:
                out["main"].append(main_model)
    return out


def evaluate(scan, expects, main_prefix, runner=None):
    problems = []
    if not expects:
        problems.append("FAIL: no --expect given; nothing to verify")
    for role, prefix in expects.items():
        seen = scan["agents"].get(role)
        if not seen:
            if runner == "codex":
                spawned = scan.get("codex_spawned_models", [])
                problems.append(
                    f"FAIL {role}: no Codex thread newer than --since has agent_role {role} or ROLE:{role} "
                    f"(unattributed spawned-thread models seen: {spawned})"
                )
            else:
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
    else:
        problems.append("FAIL: no --main given; the session model was not verified")
    return (not problems), problems


def default_project_key(cwd):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runner", choices=["claude", "codex"], required=True)
    ap.add_argument("--since", type=parse_since, default=0.0,
                     help="ISO-8601 local time; only transcripts modified at/after this count (default: all time)")
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
    if not expects:
        ap.error("at least one --expect ROLE=PREFIX is required")
    if not a.main.strip():
        ap.error("--main is required")
    since_ts = a.since

    if a.runner == "claude":
        key = a.project_key or default_project_key(os.getcwd())
        scan = scan_claude(a.claude_projects_dir, key, since_ts)
    else:
        scan = scan_codex(a.codex_sessions_dir, since_ts)

    ok, problems = evaluate(scan, expects, a.main, runner=a.runner)
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
