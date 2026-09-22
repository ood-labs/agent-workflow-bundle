from conftest import read_frontmatter


def skill(repo_root, name):
    p = repo_root / "skills" / name / "SKILL.md"
    return p, p.read_text(encoding="utf-8")


def test_delegate_skill_frontmatter_and_size(repo_root):
    p, text = skill(repo_root, "delegate")
    fm = read_frontmatter(p)
    assert fm["name"] == "delegate"
    assert fm["user-invocable"] == "true"
    assert len(text) < 25000


def test_delegate_carries_roles_map_protocol_and_spawn_phrasing(repo_root):
    _, text = skill(repo_root, "delegate")
    for needle in ["scout", "worker", "judge", "## The branching map", "## The check protocol",
                   'subagent_type: "scout"', "spawn the `worker` agent", "ROLE:scout", "ROLE:worker",
                   "jev-screen.py finding-triage", "jev-screen.py diff-risk", "git diff --stat", "max 2"]:
        assert needle in text, needle


def test_delegate_never_lets_cheap_tier_judge_or_commit(repo_root):
    _, text = skill(repo_root, "delegate")
    assert "never commit" in text.lower()
    assert "the judge is never a subagent" in text.lower()


def test_tier_check_skill_dispatches_both_roles_with_markers(repo_root):
    p, text = skill(repo_root, "tier-check")
    fm = read_frontmatter(p)
    assert fm["name"] == "tier-check"
    assert "ROLE:scout" in text and "ROLE:worker" in text
    assert "tier-check.py --runner claude" in text and "tier-check.py --runner codex" in text
    assert "--expect scout=claude-sonnet-" in text and "--expect scout=gpt-6-luna" in text
    assert "negative control" in text.lower()
