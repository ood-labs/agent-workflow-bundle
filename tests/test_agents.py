import tomllib
from conftest import read_frontmatter


def test_claude_scout_is_read_only_sonnet(repo_root):
    fm = read_frontmatter(repo_root / "agents/claude/scout.md")
    assert fm["name"] == "scout"
    assert fm["model"] == "sonnet"
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert {"Read", "Glob", "Grep"} <= tools
    assert not ({"Edit", "Write", "NotebookEdit"} & tools)
    # Claude Code cannot restrict Bash per command (a Bash(git log:*) specifier does
    # not narrow the tool), so the only safe grant for a read-only agent is no Bash
    # entry at all.
    assert "Bash" not in tools and not any(t.startswith("Bash(") for t in tools)


def test_claude_worker_edits_but_never_commits(repo_root):
    fm = read_frontmatter(repo_root / "agents/claude/worker.md")
    assert fm["name"] == "worker"
    assert fm["model"] == "sonnet"
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert {"Read", "Edit", "Write", "Glob", "Grep"} <= tools
    assert "Bash" in tools
    # No Bash(...) specifier entries: Claude Code does not enforce them, so listing
    # one would be a false sense of restriction. The git ban is prose + protocol.
    assert not any(t.startswith("Bash(") for t in tools)
    body = (repo_root / "agents/claude/worker.md").read_text(encoding="utf-8")
    assert "never run git" in body.lower()
    assert "HEAD must equal" in body


def test_codex_scout_is_luna_low_read_only(repo_root):
    t = tomllib.loads((repo_root / "agents/codex/scout.toml").read_text(encoding="utf-8"))
    assert t["name"] == "scout"
    assert t["model"] == "gpt-6-luna"
    assert t["model_reasoning_effort"] == "low"
    assert t["sandbox_mode"] == "read-only"
    assert "never edit" in t["developer_instructions"].lower()


def test_codex_worker_is_luna_medium(repo_root):
    t = tomllib.loads((repo_root / "agents/codex/worker.toml").read_text(encoding="utf-8"))
    assert t["name"] == "worker"
    assert t["model"] == "gpt-6-luna"
    assert t["model_reasoning_effort"] == "medium"
    assert "never commit" in t["developer_instructions"].lower()


def test_both_runners_agree_on_role_names(repo_root):
    claude = {read_frontmatter(p)["name"] for p in (repo_root / "agents/claude").glob("*.md")}
    codex = {tomllib.loads(p.read_text(encoding="utf-8"))["name"] for p in (repo_root / "agents/codex").glob("*.toml")}
    assert claude == codex == {"scout", "worker"}
