import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import time


def load(repo_root):
    path = repo_root / "skills/delegate/scripts/tier-check.py"
    spec = importlib.util.spec_from_file_location("tier_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def jl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def make_claude_tree(tmp_path, agent_model="claude-sonnet-5", main_model="claude-fable-5-1"):
    proj = tmp_path / "projects" / "C--repo"
    sess = proj / "s1"
    jl(proj / "s1.jsonl", [
        {"type": "assistant", "message": {"model": main_model, "content": [{"type": "tool_use", "name": "Agent",
         "input": {"subagent_type": "scout", "prompt": "ROLE:scout say ok"}}]}},
        {"type": "assistant", "message": {"model": main_model, "content": []}},
    ])
    jl(sess / "subagents" / "agent-aaa.jsonl", [
        {"type": "user", "isSidechain": True, "message": {"content": "ROLE:scout say ok"}},
        {"type": "assistant", "isSidechain": True, "message": {"model": agent_model, "content": []}},
    ])
    jl(sess / "subagents" / "agent-bbb.jsonl", [
        {"type": "user", "isSidechain": True, "message": {"content": "ROLE:worker touch nothing"}},
        {"type": "assistant", "isSidechain": True, "message": {"model": agent_model, "content": []}},
    ])
    return proj


def test_claude_scan_finds_roles_and_models(repo_root, tmp_path):
    m = load(repo_root)
    make_claude_tree(tmp_path)
    scan = m.scan_claude(tmp_path / "projects", "C--repo", since_ts=0)
    assert scan["agents"]["scout"] == ["claude-sonnet-5"]
    assert scan["agents"]["worker"] == ["claude-sonnet-5"]
    assert "claude-fable-5-1" in scan["main"]


def test_evaluate_passes_on_match(repo_root):
    m = load(repo_root)
    ok, problems = m.evaluate({"main": ["claude-fable-5-1"], "agents": {"scout": ["claude-sonnet-5"], "worker": ["claude-sonnet-5"]}},
                              {"scout": "claude-sonnet-", "worker": "claude-sonnet-"}, "claude-fable-")
    assert ok and problems == []


def test_evaluate_fails_on_wrong_model_and_names_it(repo_root):
    m = load(repo_root)
    ok, problems = m.evaluate({"main": ["claude-fable-5-1"], "agents": {"scout": ["claude-fable-5-1"], "worker": ["claude-sonnet-5"]}},
                              {"scout": "claude-sonnet-", "worker": "claude-sonnet-"}, "claude-fable-")
    assert not ok
    assert any("scout" in p and "claude-fable-5-1" in p for p in problems)


def test_evaluate_fails_when_agent_missing(repo_root):
    m = load(repo_root)
    ok, problems = m.evaluate({"main": ["claude-fable-5-1"], "agents": {"scout": ["claude-sonnet-5"]}},
                              {"scout": "claude-sonnet-", "worker": "claude-sonnet-"}, "claude-fable-")
    assert not ok and any("worker" in p and "no transcript" in p for p in problems)


def test_evaluate_fails_when_main_is_not_frontier(repo_root):
    m = load(repo_root)
    ok, problems = m.evaluate({"main": ["claude-sonnet-5"], "agents": {"scout": ["claude-sonnet-5"], "worker": ["claude-sonnet-5"]}},
                              {"scout": "claude-sonnet-", "worker": "claude-sonnet-"}, "claude-fable-")
    assert not ok and any("main" in p for p in problems)


def test_since_excludes_old_transcripts(repo_root, tmp_path):
    # Per-row semantics: a subagent file's mtime is fresh (file-level prefilter
    # passes) but its only assistant row is timestamped before --since, so it must
    # still be excluded. A row with no timestamp at all in an equally fresh file is
    # included regardless of --since.
    m = load(repo_root)
    proj = tmp_path / "projects" / "C--repo"
    sess = proj / "s1"
    since_ts = time.time()
    old_iso = dt.datetime.fromtimestamp(since_ts - 3600, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    jl(sess / "subagents" / "agent-old.jsonl", [
        {"type": "user", "isSidechain": True, "message": {"content": "ROLE:scout say ok"}},
        {"type": "assistant", "isSidechain": True, "timestamp": old_iso,
         "message": {"model": "claude-sonnet-5", "content": []}},
    ])
    jl(sess / "subagents" / "agent-no-ts.jsonl", [
        {"type": "user", "isSidechain": True, "message": {"content": "ROLE:worker touch nothing"}},
        {"type": "assistant", "isSidechain": True, "message": {"model": "claude-sonnet-5", "content": []}},
    ])
    scan = m.scan_claude(tmp_path / "projects", "C--repo", since_ts=since_ts)
    assert "scout" not in scan["agents"]
    assert scan["agents"]["worker"] == ["claude-sonnet-5"]


def test_since_rejects_garbage(repo_root, tmp_path):
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/tier-check.py"),
                        "--runner", "claude", "--since", "not-a-date",
                        "--expect", "scout=claude-sonnet-", "--main", "claude-fable-"],
                       capture_output=True, text=True)
    assert r.returncode == 2
    assert "--since" in r.stderr


def test_codex_single_file_rollout_reports_spawned_models(repo_root, tmp_path):
    m = load(repo_root)
    sessions = tmp_path / "sessions" / "2026" / "09" / "22"
    jl(sessions / "rollout-single.jsonl", [
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "t1",
         "thread_settings": {"model": "gpt-6-astra"}}},
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "t1",
         "thread_settings": {"model": "gpt-5.6-sol"}}},
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "t1",
         "thread_settings": {"model": "gpt-6-luna"}}},
    ])
    scan = m.scan_codex(tmp_path / "sessions", since_ts=0)
    assert scan["main"] == ["gpt-6-astra"]
    assert scan["codex_spawned_models"] == ["gpt-5.6-sol", "gpt-6-luna"]
    ok, problems = m.evaluate(scan, {"scout": "gpt-6-luna"}, "gpt-6-astra", runner="codex")
    assert not ok
    assert any("unverified" in p and "gpt-6-luna" in p for p in problems)


def test_codex_scan_finds_roles_and_parent(repo_root, tmp_path):
    m = load(repo_root)
    sessions = tmp_path / "sessions" / "2026" / "09" / "22"
    jl(sessions / "rollout-parent.jsonl", [
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "p", "thread_settings": {"model": "gpt-6-astra", "reasoning_effort": "high"}}},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "spawn scout ROLE:scout"}]}},
    ])
    jl(sessions / "rollout-child1.jsonl", [
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "c1", "thread_settings": {"model": "gpt-6-luna", "reasoning_effort": "low"}}},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "ROLE:scout say ok"}]}},
    ])
    jl(sessions / "rollout-child2.jsonl", [
        {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "c2", "thread_settings": {"model": "gpt-6-luna", "reasoning_effort": "medium"}}},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "ROLE:worker touch nothing"}]}},
    ])
    scan = m.scan_codex(tmp_path / "sessions", since_ts=0)
    assert scan["agents"]["scout"] == ["gpt-6-luna"]
    assert scan["agents"]["worker"] == ["gpt-6-luna"]
    assert "gpt-6-astra" in scan["main"]


def test_cli_exit_codes_positive_and_negative_control(repo_root, tmp_path):
    make_claude_tree(tmp_path)
    base = [sys.executable, str(repo_root / "skills/delegate/scripts/tier-check.py"), "--runner", "claude",
            "--since", "1970-01-01T00:00:00", "--claude-projects-dir", str(tmp_path / "projects"), "--project-key", "C--repo",
            "--main", "claude-fable-"]
    ok = subprocess.run(base + ["--expect", "scout=claude-sonnet-", "--expect", "worker=claude-sonnet-"], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "PASS" in ok.stdout
    bad = subprocess.run(base + ["--expect", "scout=claude-opus-", "--expect", "worker=claude-sonnet-"], capture_output=True, text=True)
    assert bad.returncode == 1
    assert "FAIL" in bad.stdout and "claude-sonnet-5" in bad.stdout


def test_cli_fails_when_no_evidence_at_all(repo_root, tmp_path):
    (tmp_path / "projects" / "C--repo").mkdir(parents=True)
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/tier-check.py"), "--runner", "claude",
                        "--since", "1970-01-01T00:00:00", "--claude-projects-dir", str(tmp_path / "projects"),
                        "--project-key", "C--repo", "--main", "claude-fable-", "--expect", "scout=claude-sonnet-"],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "no transcript" in r.stdout


def test_evaluate_fails_with_no_expectations(repo_root):
    m = load(repo_root)
    ok, problems = m.evaluate({"main": ["claude-fable-5-1"], "agents": {}}, {}, "claude-fable-")
    assert not ok and any("--expect" in p for p in problems)
    ok, problems = m.evaluate({"main": ["claude-fable-5-1"], "agents": {"scout": ["claude-sonnet-5"]}},
                              {"scout": "claude-sonnet-"}, "")
    assert not ok and any("--main" in p for p in problems)


def test_cli_refuses_without_expect_or_main(repo_root, tmp_path):
    base = [sys.executable, str(repo_root / "skills/delegate/scripts/tier-check.py"), "--runner", "claude",
            "--since", "1970-01-01T00:00:00", "--claude-projects-dir", str(tmp_path / "projects"),
            "--project-key", "C--repo"]
    no_expect_no_main = subprocess.run(base, capture_output=True, text=True)
    assert no_expect_no_main.returncode != 0
    assert "--expect" in no_expect_no_main.stderr
    no_main = subprocess.run(base + ["--expect", "scout=claude-sonnet-"], capture_output=True, text=True)
    assert no_main.returncode != 0
    assert "--main" in no_main.stderr


def test_default_project_key_matches_claude_format(repo_root):
    m = load(repo_root)
    # The real Claude Code key for this repo, derived from an absolute path.
    assert m.default_project_key(r"C:\Standalone\agent-workflow-bundle") == "C--Standalone-agent-workflow-bundle"
    # A relative path must be resolved first, not encoded as-is.
    assert m.default_project_key("proj") == m.default_project_key(os.path.join(os.getcwd(), "proj"))
    assert m.default_project_key("proj").endswith("-proj")
