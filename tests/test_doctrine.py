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


def test_audit_spawns_scouts_and_triages(repo_root):
    _, text = skill(repo_root, "audit")
    assert 'subagent_type: "scout"' in text or "subagent_type=scout" in text
    assert "subagent_type=Explore" not in text
    assert "jev-screen.py finding-triage" in text
    assert "Delegation follows `/delegate`" in text


def test_plan_audit_spawns_scouts_and_triages(repo_root):
    _, text = skill(repo_root, "plan-audit")
    assert 'subagent_type: "scout"' in text or "subagent_type=scout" in text
    assert "subagent_type=Explore" not in text
    assert "jev-screen.py finding-triage" in text
    assert "Delegation section" in text          # decomposition agent flags missing file list / test cmd


def test_slash_goal_default_goal_points_at_delegation(repo_root):
    _, text = skill(repo_root, "slash-goal")
    goal = text.split("```")[1]                    # the first fenced block is the default goal
    assert "Delegation section" in goal
    assert "\n" not in goal.strip()                # still one unbroken line
    assert "$wrap" in goal and " $wrap " in goal   # $ tokens still space-flanked


def test_formalize_plan_and_template_carry_delegation_section(repo_root):
    _, text = skill(repo_root, "formalize-plan")
    assert "**Delegation**" in text
    for needle in ["allowed files", "test command", "retry budget"]:
        assert needle in text, needle
    tpl = (repo_root / "skills/scaffold-project/templates/phase-template.md").read_text(encoding="utf-8")
    assert "## Delegation" in tpl and "## Autonomy & human-in-the-loop" in tpl


def test_start_session_checks_delegation_and_wrap_requires_protocol(repo_root):
    _, ss = skill(repo_root, "start-session")
    assert "Delegation section" in ss
    _, wrap = skill(repo_root, "wrap")
    assert "check protocol" in wrap
