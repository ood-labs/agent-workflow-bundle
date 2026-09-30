import re

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


def test_delegate_has_fallback_and_head_check(repo_root):
    _, text = skill(repo_root, "delegate")
    for needle in ["not a known agent type", "general-purpose", "git rev-parse HEAD", "(not yet routed)"]:
        assert needle in text, needle


def test_tier_check_refuses_fallback_and_names_the_codex_shape(repo_root):
    _, text = skill(repo_root, "tier-check")
    assert "Do not fall back" in text
    assert "agent_role" in text and "turn_context" in text
    assert "Older single-file rollouts" in text


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
    for tok in ("$start-session", "$wrap", "$audit", "$end-session"):
        assert tok in goal, tok
    for m in re.finditer(r"\$[a-z][a-z-]*", goal):
        assert m.end() == len(goal) or goal[m.end()].isspace(), f"{m.group(0)} touches punctuation"


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


def test_audit_playbooks_uses_scouts_not_explore(repo_root):
    p, text = skill(repo_root, "audit-playbooks")
    assert "Explore" not in text
    assert 'subagent_type: "scout"' in text
    assert "ROLE:scout" in text
    assert "Delegation follows `/delegate`" in text


def test_docs_mention_delegate_and_tier_check(repo_root):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "`/delegate`" in readme and "`/tier-check`" in readme
    assert "Codex multi_agent v2" in readme
    workflow = (repo_root / "WORKFLOW.md").read_text(encoding="utf-8")
    assert "scout" in workflow and "worker" in workflow and "check protocol" in workflow
    assert "cannot restrict Bash per command" in workflow
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8")
    assert "<root>/agents/" in install and "CLAUDE_CODE_SUBAGENT_MODEL" in install and "default_subagent_model" in install
    assert "Restart the agent first" in install
    agents_md = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "`agents/claude/`" in agents_md and "`skills/delegate/`" in agents_md and "/tier-check" in agents_md


def test_docs_never_describe_a_skill_as_using_explore(repo_root):
    # "Explore" may appear only in a prohibition (never use it), never in a
    # description of what a skill does.
    PROHIBITION = ("never", "not ", "defect", "instead")
    for name in ("README.md", "WORKFLOW.md", "INSTALL.md", "AGENTS.md"):
        text = (repo_root / name).read_text(encoding="utf-8")
        assert "4-agent" not in text, name
        assert "3-agent" not in text, name
        for i, line in enumerate(text.splitlines(), 1):
            if "Explore" in line:
                assert any(p in line.lower() for p in PROHIBITION), \
                    f"{name}:{i} describes a skill as using Explore: {line.strip()}"
    agents_md = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "no test suite" not in agents_md
    assert "pytest tests -q" in agents_md


def test_docs_never_pin_the_judge_to_a_named_model(repo_root):
    # The judge is a tier: whatever frontier model the session runs. Naming one
    # makes a correct run look wrong when the session is on a different model.
    NAMED = ("Fable", "Astra", "Opus", "Sonnet 5 is the judge")
    targets = [
        repo_root / "skills/delegate/SKILL.md",
        repo_root / "skills/tier-check/SKILL.md",
        repo_root / "WORKFLOW.md",
        repo_root / "README.md",
        repo_root / "docs/superpowers/specs/2026-09-22-model-tiering-design.md",
    ]
    for p in targets:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "judge" not in line.lower():
                continue
            for name in NAMED:
                assert name not in line, f"{p.name}:{i} pins the judge to {name}: {line.strip()}"
