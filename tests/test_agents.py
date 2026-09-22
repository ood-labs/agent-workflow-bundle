import tomllib
from conftest import read_frontmatter

MUTATING = ("git commit", "git add", "git push", "git reset", "git checkout", "git merge", "git rebase", "git tag")


def test_claude_scout_is_read_only_sonnet(repo_root):
    fm = read_frontmatter(repo_root / "agents/claude/scout.md")
    assert fm["name"] == "scout"
    assert fm["model"] == "sonnet"
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert {"Read", "Glob", "Grep"} <= tools
    assert not ({"Edit", "Write", "NotebookEdit"} & tools)
    assert "Bash" not in tools, "unrestricted Bash would allow mutation"
    assert not any(t.startswith(f"Bash({m}") for m in MUTATING for t in tools)


def test_claude_worker_edits_but_never_commits(repo_root):
    fm = read_frontmatter(repo_root / "agents/claude/worker.md")
    assert fm["name"] == "worker"
    assert fm["model"] == "sonnet"
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert {"Read", "Edit", "Write", "Glob", "Grep"} <= tools
    assert "Bash" not in tools, "unrestricted Bash would allow git commit"
    assert not any(t.startswith(f"Bash({m}") for m in MUTATING for t in tools)


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
