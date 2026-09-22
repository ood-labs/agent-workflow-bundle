import os
import shutil
import subprocess
import sys
import pytest

PWSH = shutil.which("pwsh")
BASH = shutil.which("bash")


def run_sh(repo_root, home, target, env_extra=None):
    env = dict(os.environ, HOME=str(home))
    env.update(env_extra or {})
    return subprocess.run([BASH, str(repo_root / "scripts/install.sh"), target],
                          capture_output=True, text=True, env=env)


def run_ps1(repo_root, home, args):
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home))
    return subprocess.run([PWSH, "-NoProfile", "-File", str(repo_root / "scripts/install.ps1"), *args],
                          capture_output=True, text=True, env=env)


@pytest.mark.skipif(BASH is None, reason="bash not on PATH")
def test_sh_installs_agents_per_target(repo_root, tmp_path):
    r = run_sh(repo_root, tmp_path, "all")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / ".claude/agents/scout.md").is_file()
    assert (tmp_path / ".claude/agents/worker.md").is_file()
    assert (tmp_path / ".codex/agents/scout.toml").is_file()
    assert (tmp_path / ".codex/agents/worker.toml").is_file()
    assert not (tmp_path / ".agents/agents").exists()
    assert "Config snippets (not written)" in r.stdout
    assert "CLAUDE_CODE_SUBAGENT_MODEL" in r.stdout
    assert 'default_subagent_model = "gpt-6-luna"' in r.stdout


@pytest.mark.skipif(BASH is None, reason="bash not on PATH")
def test_sh_dry_run_lists_agents_and_writes_nothing(repo_root, tmp_path):
    r = run_sh(repo_root, tmp_path, "claude", {"DRY_RUN": "1"})
    assert r.returncode == 0, r.stderr
    assert "agents/scout.md" in r.stdout
    assert not (tmp_path / ".claude").exists()


@pytest.mark.skipif(BASH is None, reason="bash not on PATH")
def test_sh_refuses_agent_conflict(repo_root, tmp_path):
    (tmp_path / ".codex/agents").mkdir(parents=True)
    (tmp_path / ".codex/agents/scout.toml").write_text("stale", encoding="utf-8")
    r = run_sh(repo_root, tmp_path, "codex")
    assert r.returncode != 0
    assert "scout.toml" in r.stderr
    assert (tmp_path / ".codex/agents/scout.toml").read_text(encoding="utf-8") == "stale"


@pytest.mark.skipif(BASH is None, reason="bash not on PATH")
def test_sh_never_touches_settings_or_config(repo_root, tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".claude/settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".codex/config.toml").write_text("model = \"x\"\n", encoding="utf-8")
    r = run_sh(repo_root, tmp_path, "all")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / ".claude/settings.json").read_text(encoding="utf-8") == "{}"
    assert (tmp_path / ".codex/config.toml").read_text(encoding="utf-8") == "model = \"x\"\n"


@pytest.mark.skipif(PWSH is None, reason="pwsh not on PATH")
def test_ps1_installs_agents_per_target(repo_root, tmp_path):
    r = run_ps1(repo_root, tmp_path, ["-Target", "all"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert (tmp_path / ".claude/agents/scout.md").is_file()
    assert (tmp_path / ".codex/agents/worker.toml").is_file()
    assert not (tmp_path / ".agents/agents").exists()
    assert "Config snippets (not written)" in r.stdout


@pytest.mark.skipif(PWSH is None, reason="pwsh not on PATH")
def test_ps1_refuses_agent_conflict(repo_root, tmp_path):
    (tmp_path / ".claude/agents").mkdir(parents=True)
    (tmp_path / ".claude/agents/worker.md").write_text("stale", encoding="utf-8")
    r = run_ps1(repo_root, tmp_path, ["-Target", "claude"])
    assert r.returncode != 0
    assert "worker.md" in (r.stderr + r.stdout)
    assert (tmp_path / ".claude/agents/worker.md").read_text(encoding="utf-8") == "stale"
