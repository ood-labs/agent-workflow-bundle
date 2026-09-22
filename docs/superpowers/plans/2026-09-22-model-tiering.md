# Model Tiering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship named `scout` / `worker` agents on both runners, the `/delegate` doctrine, two Jev screens, a transcript-based `/tier-check`, the skill and doc edits that route menial work to the cheap tier, and a test suite that proves each piece and can fail.

**Architecture:** Agent definitions are data files shipped in `agents/` and installed next to skills. Doctrine lives in `skills/delegate/SKILL.md`; other skills cite it. Two stdlib-only Python helpers (`jev-screen.py`, `tier-check.py`) live inside `skills/delegate/scripts/` so they travel with the skill. A `tests/` folder with pytest covers the helpers, the installers, the agent files, and the doctrine strings the skills must carry.

**Tech Stack:** Markdown skills, Python 3.12 stdlib (`json`, `urllib`, `tomllib`, `argparse`), pytest 9, PowerShell 7 and bash installers.

**Spec:** `docs/superpowers/specs/2026-09-22-model-tiering-design.md`

## Global Constraints

- Cheap tier is exactly: Claude Code `model: sonnet`; Codex `model = "gpt-6-luna"` (scout `model_reasoning_effort = "low"`, worker `"medium"`).
- Judge is always the session itself. No skill may delegate synthesis, plan edits, approval, or any git operation.
- Helpers are stdlib only, exit 0 on any environmental failure with a line starting `skipped: ` (jev-screen) — except `tier-check.py`, whose whole purpose is to fail: it exits 1 on mismatch or missing evidence.
- The installer never writes `settings.json` or `config.toml`; it prints snippets.
- Never write `TYPESAFE_API_KEY` into any file.
- Skill prose: imperative, tight, matches neighbours. `/delegate` SKILL.md under 25,000 characters.
- Commits: conventional (`feat(delegate): …`, `test: …`, `docs: …`), explicit paths, no `git add -A`, footer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Tests run with `python -m pytest tests -q` from the repo root and must pass before each commit.

---

## File structure

| Path | Responsibility |
|---|---|
| `agents/claude/scout.md`, `agents/claude/worker.md` | Claude Code agent definitions |
| `agents/codex/scout.toml`, `agents/codex/worker.toml` | Codex agent definitions |
| `skills/delegate/SKILL.md` | Roles, branching map, check protocol, how to name a role per runner |
| `skills/delegate/scripts/jev-screen.py` | `finding-triage` and `diff-risk` screens; JSON in on stdin, JSON out |
| `skills/delegate/scripts/tier-check.py` | Asserts which model each agent ran on, from transcripts |
| `skills/tier-check/SKILL.md` | User-invocable proof run |
| `scripts/install.ps1`, `scripts/install.sh` | Also install `agents/`, print config snippets |
| `tests/conftest.py`, `tests/test_agents.py`, `tests/test_installers.py`, `tests/test_jev_screen.py`, `tests/test_tier_check.py`, `tests/test_doctrine.py` | pytest suite |
| skill edits | `audit`, `plan-audit`, `slash-goal`, `formalize-plan`, `start-session`, `wrap`, `scaffold-project/templates/phase-template.md` |
| docs | `README.md`, `WORKFLOW.md`, `INSTALL.md`, `AGENTS.md` |

---

### Task 1: Agent definitions and their tests

**Files:**
- Create: `agents/claude/scout.md`, `agents/claude/worker.md`, `agents/codex/scout.toml`, `agents/codex/worker.toml`
- Create: `tests/conftest.py`, `tests/test_agents.py`

**Interfaces:**
- Produces: agent names `scout` and `worker`, identical on both runners. Later skills spawn them by these names.
- Produces: `tests/conftest.py` fixture `repo_root` (pathlib.Path to the bundle root) used by every later test file.

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py`:

```python
import pathlib
import pytest


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def read_frontmatter(path: pathlib.Path) -> dict:
    """Parse the YAML-ish frontmatter block of a markdown file into a flat dict.
    Only `key: value` lines are supported; that is all the bundle uses."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    end = text.index("\n---", 4)
    block = text[4:end]
    out = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out
```

`tests/test_agents.py`:

```python
import tomllib
from conftest import read_frontmatter

# Read-only git (log, show, diff) is allowed for both roles; these are not.
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_agents.py -q`
Expected: 5 failures, `FileNotFoundError` on `agents/claude/scout.md`.

- [ ] **Step 3: Write the four agent files**

`agents/claude/scout.md`:

```markdown
---
name: scout
description: Cheap-tier reader. Collects evidence, searches, reads docs, and reports with file:line citations. Never edits, never decides. Spawn one per audit lens or per lookup; the session (the judge) synthesizes.
model: sonnet
tools: Read, Glob, Grep, Bash(git log:*), Bash(git show:*), Bash(git diff:*), Bash(ls:*), Bash(cat:*), Bash(ctest:*), WebFetch, WebSearch
---

You are a **scout**: a read-only reporter working for a more capable session that will judge your report. You never edit, write, commit, or decide anything.

Rules:
1. Report facts with `file:line` citations. Every claim you make must be traceable to something you read this run.
2. Separate what you verified from what you infer. Label inferences.
3. Rank findings, most important first. Under 800 words unless the prompt sets another limit.
4. If you cannot verify something, say "unverified" and why. Never fill a gap with a plausible guess.
5. Never run anything that mutates state. If the task seems to need that, report it as a blocker.

Report shape:

```
Findings (ranked):
1. <claim> | <file:line> | verified|inferred
...
Unverified:
- <what and why>
```
```

`agents/claude/worker.md`:

```markdown
---
name: worker
description: Cheap-tier implementer. Takes ONE sub-slice from a phase doc, edits only the files that slice names, runs the slice's test command, and reports files touched + test output + evidence. Never commits, never edits plans or instruction files. The session (the judge) verifies before /wrap.
model: sonnet
tools: Read, Edit, Write, Glob, Grep, Bash(cargo test:*), Bash(cargo build:*), Bash(npm test:*), Bash(npm run:*), Bash(python -m pytest:*), Bash(pytest:*), Bash(ctest:*), Bash(cmake:*), Bash(ls:*), Bash(cat:*)
---

You are a **worker**: you implement one bounded sub-slice for a more capable session that will verify your work before it is committed.

Your prompt names: the sub-slice, its pass criterion, the files you may touch, and the test command. Treat those as hard limits.

Rules:
1. Touch only the listed files. If the task needs another file, stop and report it as a blocker instead of editing it.
2. Never run git. Never edit `AGENTS.md`, `CLAUDE.md`, anything under `docs/phases/`, `docs/design/`, or `docs/implementation-plan.md`.
3. Run the test command yourself before reporting. Paste its real output.
4. Report honestly: what passes, what does not, what you skipped and why.

Report shape:

```
Files touched: <exact paths>
Test command: <as run>
Test output: <verbatim tail>
Pass criterion evidence: <how the criterion is met, or why it is not>
Blockers / unresolved: <list or "none">
```
```

`agents/codex/scout.toml`:

```toml
name = "scout"
description = "Cheap-tier reader. Collects evidence, searches, reads docs, reports with file:line citations. Never edits, never decides. Spawn one per audit lens or per lookup; the parent session synthesizes."
model = "gpt-6-luna"
model_reasoning_effort = "low"
sandbox_mode = "read-only"
developer_instructions = """
You are a scout: a read-only reporter working for a more capable session that will judge your report. You NEVER edit, write, commit, or decide anything.

1. Report facts with file:line citations traceable to something you read this run.
2. Separate verified from inferred; label inferences.
3. Rank findings, most important first. Under 800 words unless told otherwise.
4. If you cannot verify something, say "unverified" and why. Never guess.
5. Never run anything that mutates state; report it as a blocker instead.

Report shape:
Findings (ranked): 1. <claim> | <file:line> | verified|inferred ...
Unverified: - <what and why>
"""
```

`agents/codex/worker.toml`:

```toml
name = "worker"
description = "Cheap-tier implementer. Takes ONE sub-slice from a phase doc, edits only the files that slice names, runs the slice's test command, reports files touched + test output + evidence. Never commits, never edits plans or instruction files. The parent session verifies before wrap."
model = "gpt-6-luna"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
developer_instructions = """
You are a worker: you implement one bounded sub-slice for a more capable session that verifies your work before it is committed.

Your prompt names the sub-slice, its pass criterion, the files you may touch, and the test command. Treat those as hard limits.

1. Touch only the listed files. If another file is needed, stop and report a blocker; do not edit it.
2. NEVER run git. NEVER commit. Never edit AGENTS.md, CLAUDE.md, docs/phases/, docs/design/, or docs/implementation-plan.md.
3. Run the test command yourself before reporting; paste its real output.
4. Report honestly: what passes, what does not, what you skipped and why.

Report shape:
Files touched: <exact paths>
Test command: <as run>
Test output: <verbatim tail>
Pass criterion evidence: <how met, or why not>
Blockers / unresolved: <list or "none">
"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_agents.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add agents/claude/scout.md agents/claude/worker.md agents/codex/scout.toml agents/codex/worker.toml tests/conftest.py tests/test_agents.py
git commit -m "feat(agents): scout and worker definitions for Claude Code and Codex, cheap tier pinned"
```

---

### Task 2: Installers copy agents and print config snippets

**Files:**
- Modify: `scripts/install.ps1` (whole file; current version is 189 lines)
- Modify: `scripts/install.sh` (whole file; current version is 136 lines)
- Create: `tests/test_installers.py`

**Interfaces:**
- Consumes: `agents/claude/*.md`, `agents/codex/*.toml` from Task 1.
- Produces: installed `<root>/agents/scout.md` + `worker.md` for the `claude` target, `<root>/agents/scout.toml` + `worker.toml` for the `codex` target, nothing for `agents` target (the agent-neutral root has no agent runtime). Stdout ends with a `Config snippets (not written)` section.

- [ ] **Step 1: Write the failing tests**

`tests/test_installers.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_installers.py -q`
Expected: the "installs agents" and "dry run lists agents" and "refuses agent conflict" tests fail (agents dir never created / conflict not detected). The "never touches settings" test may already pass; that is fine.

- [ ] **Step 3: Extend `scripts/install.sh`**

Add after `playbooks_source="$bundle_root/playbooks"`:

```bash
agents_source="$bundle_root/agents"

# Which agent-definition subfolder a target consumes. The agent-neutral root has no runtime.
agents_subdir_for() {
  case "$1" in
    claude) echo "claude" ;;
    codex)  echo "codex" ;;
    *)      echo "" ;;
  esac
}
```

In the conflict-scan loop, after the playbooks `for`, add:

```bash
    sub="$(agents_subdir_for "$name")"
    if [[ -n "$sub" && -d "$agents_source/$sub" ]]; then
      for agent in "$agents_source/$sub"/*; do
        [[ -f "$agent" ]] || continue
        destination="$root/agents/$(basename "$agent")"
        [[ ! -e "$destination" ]] || conflicts+=("$destination")
      done
    fi
```

In the install loop, after the playbooks `for`, add:

```bash
  sub="$(agents_subdir_for "$name")"
  if [[ -n "$sub" && -d "$agents_source/$sub" ]]; then
    agents_dest="$root/agents"
    if [[ "$dry_run" == "1" ]]; then
      echo "[dry-run] ensure $agents_dest"
    else
      mkdir -p -- "$agents_dest"
    fi
    for agent in "$agents_source/$sub"/*; do
      [[ -f "$agent" ]] || continue
      copy_file "$agent" "$agents_dest/$(basename "$agent")"
    done
    echo "  agents: $agents_dest"
  fi
```

At the very end of the file append:

```bash
cat <<'EOF'

Config snippets (not written) - add by hand so unnamed subagents also land on the cheap tier:

  Claude Code  ~/.claude/settings.json
    "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet" }

  Codex        ~/.codex/config.toml
    [agents]
    default_subagent_model = "gpt-6-luna"
    default_subagent_reasoning_effort = "low"
EOF
```

- [ ] **Step 4: Extend `scripts/install.ps1`**

After `$playbooksSource = Join-Path $bundleRoot "playbooks"` add:

```powershell
$agentsSource = Join-Path $bundleRoot "agents"

function Get-AgentsSubdir {
    param([string]$TargetName)
    switch ($TargetName) {
        "claude" { return "claude" }
        "codex"  { return "codex" }
        default  { return $null }
    }
}
```

In the conflict scan `foreach ($targetInfo in $targetInfos)` block, after the playbooks loop add:

```powershell
        $sub = Get-AgentsSubdir $targetInfo.Name
        if ($sub -and (Test-Path -LiteralPath (Join-Path $agentsSource $sub))) {
            foreach ($agent in Get-ChildItem -LiteralPath (Join-Path $agentsSource $sub) -File) {
                $dest = Join-Path (Join-Path $targetRoot "agents") $agent.Name
                if (Test-Path -LiteralPath $dest) { $conflicts += $dest }
            }
        }
```

In the install loop, after the playbooks `foreach` add:

```powershell
    $sub = Get-AgentsSubdir $targetName
    if ($sub -and (Test-Path -LiteralPath (Join-Path $agentsSource $sub))) {
        $agentsDest = Join-Path $targetRoot "agents"
        if ($DryRun) { Write-Host "[dry-run] ensure $agentsDest" }
        else { New-Item -ItemType Directory -Force -Path $agentsDest | Out-Null }
        foreach ($agent in Get-ChildItem -LiteralPath (Join-Path $agentsSource $sub) -File) {
            Copy-FileItem -Source $agent.FullName -Destination (Join-Path $agentsDest $agent.Name) -Overwrite $Overwrite -DryRun $DryRun
        }
    }
```

Add `Agents = $(if ($sub) { Join-Path $targetRoot "agents" } else { "-" })` to the `[pscustomobject]` summary. At the end of the file append:

```powershell
Write-Host ""
Write-Host "Config snippets (not written) - add by hand so unnamed subagents also land on the cheap tier:"
Write-Host ""
Write-Host '  Claude Code  ~/.claude/settings.json'
Write-Host '    "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet" }'
Write-Host ""
Write-Host '  Codex        ~/.codex/config.toml'
Write-Host '    [agents]'
Write-Host '    default_subagent_model = "gpt-6-luna"'
Write-Host '    default_subagent_reasoning_effort = "low"'
```

Note for Windows: `Get-HomePath` already prefers `$env:USERPROFILE`, which the test overrides. The conflict `throw` message must include the path (it does: `$message` lists `$conflicts`).

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_installers.py -q`
Expected: all pass (or skipped where a shell is absent; on this machine both bash and pwsh exist, so 6 passed).

- [ ] **Step 6: Commit**

```bash
git add scripts/install.ps1 scripts/install.sh tests/test_installers.py
git commit -m "feat(install): copy scout/worker agent definitions per runner, print cheap-tier config snippets"
```

---

### Task 3: `jev-screen.py` with finding-triage and diff-risk

**Files:**
- Create: `skills/delegate/scripts/jev-screen.py`
- Create: `tests/test_jev_screen.py`

**Interfaces:**
- Produces CLI: `python jev-screen.py <finding-triage|diff-risk> [--json]` reading a JSON document on stdin.
  - `finding-triage` input: `{"doctrine": "<apply-now criterion text>", "findings": [{"id": "f1", "agent": "...", "claim": "...", "proposed_change": "...", "citation": "..."}]}`
  - `diff-risk` input: `{"slice": {"id": "4.1b", "pass_criterion": "...", "allowed_files": [...]}, "hunks": [{"id": "h1", "file": "...", "summary": "..."}]}`
- Produces output (always exit 0): either `{"skipped": "<reason>"}` or, for finding-triage, `{"usage": {...}, "rows": [{"id", "bucket", "bucket_confidence", "safe_to_auto_apply", "verdict"}]}` with `verdict` in `AUTO_APPLY | REVIEW | ASK`; for diff-risk, `{"usage": {...}, "slice_status": "...", "slice_confidence": 0.0, "rows": [{"id", "file", "needs_close_review", "order"}]}` where `order` is 1-based descending by `needs_close_review`.
- Produces importable functions for tests: `build_questions(mode, doc)`, `decide_finding(bucket, bucket_conf, safe)`, `decide_diff(answers, hunks)`, `call_api(key, state, questions)` (monkeypatched in tests).
- Policy constants: `AUTO_APPLY` iff `safe >= 0.8 and bucket == "derived_fix" and bucket_conf >= 0.6`; `ASK` iff `bucket == "unresolvable"` or `bucket == "unclear"`; else `REVIEW`.

- [ ] **Step 1: Write the failing tests**

`tests/test_jev_screen.py`:

```python
import importlib.util
import json
import subprocess
import sys


def load_module(repo_root):
    path = repo_root / "skills/delegate/scripts/jev-screen.py"
    spec = importlib.util.spec_from_file_location("jev_screen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_finding_triage_policy_matrix(repo_root):
    m = load_module(repo_root)
    assert m.decide_finding("derived_fix", 0.9, 0.95) == "AUTO_APPLY"
    assert m.decide_finding("derived_fix", 0.9, 0.79) == "REVIEW"      # not safe enough
    assert m.decide_finding("derived_fix", 0.5, 0.95) == "REVIEW"      # bucket not confident
    assert m.decide_finding("judgement_call", 0.9, 0.95) == "REVIEW"   # never auto-apply a judgement
    assert m.decide_finding("unresolvable", 0.9, 0.95) == "ASK"
    assert m.decide_finding("unclear", 0.2, 0.1) == "ASK"


def test_finding_triage_questions_cover_every_finding(repo_root):
    m = load_module(repo_root)
    doc = {"doctrine": "small, mechanical", "findings": [{"id": "f1", "claim": "a"}, {"id": "f2", "claim": "b"}]}
    qs = m.build_questions("finding-triage", doc)
    assert set(qs) == {"bucket_f1", "safe_f1", "bucket_f2", "safe_f2"}
    assert qs["bucket_f1"]["type"] == "choice"
    assert "unclear" in qs["bucket_f1"]["criteria"] and "unresolvable" in qs["bucket_f1"]["criteria"]
    assert qs["safe_f1"]["type"] == "noul"
    assert "`findings[0]" in qs["bucket_f1"]["instructions"]


def test_diff_risk_orders_hunks_and_reports_status(repo_root):
    m = load_module(repo_root)
    hunks = [{"id": "h1", "file": "a.py", "summary": "rename"}, {"id": "h2", "file": "b.py", "summary": "new auth path"}]
    answers = {
        "risk_h1": {"type": "noul", "noul": 0.2},
        "risk_h2": {"type": "noul", "noul": 0.9},
        "slice_status": {"type": "choice", "choice": "partial", "confidence": 0.7, "probabilities": {}},
    }
    out = m.decide_diff(answers, hunks)
    assert out["slice_status"] == "partial"
    assert [r["id"] for r in sorted(out["rows"], key=lambda r: r["order"])] == ["h2", "h1"]


def test_cli_skips_without_key(repo_root, tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "diff-risk"],
                       input=json.dumps({"slice": {}, "hunks": []}), capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)["skipped"].startswith("TYPESAFE_API_KEY")


def test_cli_skips_on_bad_input(repo_root, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "finding-triage"],
                       input="not json", capture_output=True, text=True)
    assert r.returncode == 0
    assert "skipped" in json.loads(r.stdout)


def test_cli_skips_on_api_failure(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def boom(key, state, questions):
        raise OSError("no network")
    m.call_api = boom
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"id": "f1", "claim": "c"}]})
    assert out["skipped"].startswith("API unreachable")


def test_run_finding_triage_with_fake_api(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def fake(key, state, questions):
        return {"usage": {"input_tokens": 10}, "answers": {
            "bucket_f1": {"type": "choice", "choice": "derived_fix", "confidence": 0.9, "probabilities": {}},
            "safe_f1": {"type": "noul", "noul": 0.95}}}
    m.call_api = fake
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"id": "f1", "claim": "c"}]})
    assert out["rows"][0]["verdict"] == "AUTO_APPLY"
    assert out["usage"]["input_tokens"] == 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_jev_screen.py -q`
Expected: all fail with `FileNotFoundError` from `load_module`.

- [ ] **Step 3: Write `skills/delegate/scripts/jev-screen.py`**

```python
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
        rows.append({"id": h["id"], "file": h.get("file", ""), "needs_close_review": round(float(a.get("noul", 1.0)), 2)})
    for order, r in enumerate(sorted(rows, key=lambda r: -r["needs_close_review"]), start=1):
        r["order"] = order
    s = answers.get("slice_status", {})
    return {"slice_status": s.get("choice", "unclear"), "slice_confidence": round(float(s.get("confidence", 0.0)), 2), "rows": rows}


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
    answers = resp.get("answers", {})
    out = {"usage": resp.get("usage", {})}
    if mode == "finding-triage":
        rows = []
        for f in doc["findings"]:
            b = answers.get(f"bucket_{f['id']}", {})
            s = answers.get(f"safe_{f['id']}", {})
            bucket = b.get("choice", "unclear")
            conf = float(b.get("confidence", 0.0))
            safe = float(s.get("noul", 0.0))
            rows.append({"id": f["id"], "bucket": bucket, "bucket_confidence": round(conf, 2),
                         "safe_to_auto_apply": round(safe, 2), "verdict": decide_finding(bucket, conf, safe)})
        out["rows"] = rows
    else:
        out.update(decide_diff(answers, doc["hunks"]))
    return out


def main(argv):
    if not argv or argv[0] not in ("finding-triage", "diff-risk"):
        print(__doc__)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_jev_screen.py -q`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/delegate/scripts/jev-screen.py tests/test_jev_screen.py
git commit -m "feat(delegate): jev-screen helper with finding-triage and diff-risk screens"
```

---

### Task 4: `tier-check.py` transcript assertion

**Files:**
- Create: `skills/delegate/scripts/tier-check.py`
- Create: `tests/test_tier_check.py`

**Interfaces:**
- Produces CLI:
  `python tier-check.py --runner claude --since <ISO8601> --expect scout=claude-sonnet- --expect worker=claude-sonnet- --main claude-fable- [--claude-projects-dir DIR] [--project-key KEY] [--json]`
  `python tier-check.py --runner codex --since <ISO8601> --expect scout=gpt-6-luna --expect worker=gpt-6-luna --main gpt-6-astra [--codex-sessions-dir DIR] [--json]`
- `--expect NAME=PREFIX` may repeat. Match is prefix on the model string.
- Exit 0 only when every expected agent has at least one transcript newer than `--since` whose every model string matches its prefix AND the main/parent model matches `--main`. Exit 1 on any mismatch or missing evidence, printing one `FAIL` line per problem with the model actually seen.
- Claude evidence: files `<projects_dir>/<project_key>/*/subagents/agent-*.jsonl` with mtime >= since; the agent's role is identified by the `subagent_type` in the parent transcript's `Agent` tool_use whose `agentId` matches the file name; fallback: the first user line of the subagent file must contain `ROLE:<name>` (the `/tier-check` skill puts that marker in each prompt so identification never depends on the parent transcript format).
- Codex evidence: `<sessions_dir>/**/*.jsonl` with mtime >= since containing `thread_settings_applied` events; the role is identified by `ROLE:<name>` appearing in a later user/agent message in the same file, and the parent is the file that contains the spawn (the one whose first `thread_settings_applied` has `--main`'s model).

Importable for tests: `scan_claude(projects_dir, project_key, since_ts)` and `scan_codex(sessions_dir, since_ts)` both return `{"main": [models...], "agents": {role: [models...]}}`; `evaluate(scan, expects, main_prefix)` returns `(ok: bool, problems: list[str])`.

- [ ] **Step 1: Write the failing tests**

`tests/test_tier_check.py`:

```python
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
    m = load(repo_root)
    proj = make_claude_tree(tmp_path)
    old = time.time() - 3600
    for p in (proj / "s1" / "subagents").glob("*.jsonl"):
        os.utime(p, (old, old))
    scan = m.scan_claude(tmp_path / "projects", "C--repo", since_ts=time.time() - 60)
    assert scan["agents"] == {}


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tier_check.py -q`
Expected: all fail with `FileNotFoundError`.

- [ ] **Step 3: Write `skills/delegate/scripts/tier-check.py`**

```python
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
    return dt.datetime.fromisoformat(s).timestamp()


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_tier_check.py -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/delegate/scripts/tier-check.py tests/test_tier_check.py
git commit -m "feat(delegate): tier-check asserts agent models from transcripts, fails on missing evidence"
```

---

### Task 5: `/delegate` doctrine and `/tier-check` skill

**Files:**
- Create: `skills/delegate/SKILL.md`
- Create: `skills/tier-check/SKILL.md`
- Create: `tests/test_doctrine.py` (first half; Task 6 adds to it)

**Interfaces:**
- Produces: the sentence other skills use to cite the doctrine: "Delegation follows `/delegate`: scouts read, workers implement inside their slice, the session judges, Jev screens."
- Produces: the runner-specific spawn phrasing every skill copies:
  - Claude Code: `Agent` tool with `subagent_type: "scout"` (or `"worker"`); put `ROLE:scout` / `ROLE:worker` as the first token of the prompt.
  - Codex: "spawn the `scout` agent" / "spawn the `worker` agent" in the instruction; put `ROLE:scout` / `ROLE:worker` as the first token of the spawn prompt.

- [ ] **Step 1: Write the failing tests**

`tests/test_doctrine.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_doctrine.py -q`
Expected: 4 failures, `FileNotFoundError`.

- [ ] **Step 3: Write `skills/delegate/SKILL.md`**

```markdown
---
name: delegate
description: The bundle's model-tiering doctrine. Cheap-tier scouts read and report, cheap-tier workers implement one sub-slice each, the session (Fable on Claude Code, Astra on Codex) is the only judge, and Jev screens every handoff. Other skills cite this; invoke it directly to see the branching map, the check protocol, or how to name a role on each runner.
allowed-tools: Read, Glob, Grep, Bash(python:*), Bash(git diff:*), Bash(git status:*)
user-invocable: true
---

# Delegate

One sentence other skills use: **Delegation follows `/delegate`: scouts read, workers implement inside their slice, the session judges, Jev screens.**

## Roles

| Role | May | May never | Claude Code | Codex |
|---|---|---|---|---|
| **scout** | read, search, run read-only commands, fetch docs, report with `file:line` | edit, write, commit, decide | agent `scout`, `model: sonnet` | agent `scout`, `gpt-6-luna` low |
| **worker** | edit files inside its assigned sub-slice, run that slice's tests, draft a doc, report files + test output + evidence | touch files outside the slice, edit plans or instruction files, commit, push, approve | agent `worker`, `model: sonnet` | agent `worker`, `gpt-6-luna` medium |
| **judge** | orient, author, synthesize, verify, apply, approve, commit | delegate a judgment | the session | the session |
| **screen** | return calibrated typed answers at handoffs | execute anything | Jev via `TYPESAFE_API_KEY`, optional | same |

The judge is never a subagent. Workers never commit. If a skill needs a judgment, it runs it in the session.

Safety net: `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` (Claude settings `env`) and `[agents] default_subagent_model = "gpt-6-luna"` (Codex config) catch any spawn that forgot to name a role. The installer prints these; add them by hand.

## How to name a role

- **Claude Code**: call the `Agent` tool with `subagent_type: "scout"` or `subagent_type: "worker"`. Start the prompt with `ROLE:scout` or `ROLE:worker` so `/tier-check` can identify the transcript.
- **Codex**: write "spawn the `scout` agent" or "spawn the `worker` agent" in the instruction, and start the spawn prompt with `ROLE:scout` / `ROLE:worker`.
- Both: the prompt is self-contained (the agent has not seen the conversation), names the exact files, and for a worker names the pass criterion, the allowed files, and the test command.

## The branching map

```
                 JUDGE (session)                   CHEAP TIER                                SCREEN (Jev)
/start-session   orient, planning audit            -                                         -
/formalize-plan  author the contract               -                                         -
/spec-draft
/research-prompt

/plan-audit      read ctx ---------------------->  5 scouts, one per lens, report -------->  proof-altitude
                 fix plan <-- ranked findings <----------------------------------------- finding-triage
/audit           scope diff -------------------->  3 scouts report ---------------------->  finding-triage
                 apply safe / surface rest <------------------------------------------------

slash-goal loop  per sub-slice the phase doc marks delegable:
                 dispatch slice ---------------->  worker implements + runs tests
                 CHECK (below)              <----  files, test output, evidence
                                                                                        diff-risk
                 accept -> /wrap  |  reject -> re-dispatch (max 2) -> then do it itself
/wrap /checkpoint /end-session   judge only

/lookup /find-session            scout collects -> judge summarizes
/audit-playbooks deep            scouts verify claims -> judge decides
/extract-playbook /slim          worker drafts the file -> judge reviews, applies
```

Rows that stay on the judge stay there because orientation and plan authoring are the judgment itself, and the closers need the session's own memory and own every git operation.

## The check protocol

A worker's report is a claim, not evidence. Before anything a worker did reaches `/wrap`:

1. **Scope.** Run `git diff --stat` and compare with the files the worker says it touched and the slice's allowed files. Any file outside the slice: reject without reading further.
2. **Tests.** Run the slice's test command yourself. The worker's pasted output does not count.
3. **Screen.** Build `{"slice": {...}, "hunks": [{"id","file","summary"}]}` from the diff (one hunk per file or per logical change, a one-line summary each) and pipe it to `python <delegate skill base dir>/scripts/jev-screen.py diff-risk`. It returns `needs_close_review` per hunk and a `slice_status`. If it prints `skipped:`, read in file order instead.
4. **Read.** Every hunk, in descending `needs_close_review`. The screen orders; it never excuses a hunk.
5. **Decide.** `meets_criterion` and you agree after reading: proceed to `/wrap`. Otherwise re-dispatch the worker with your findings as the prompt (same role, same slice, same limits). After **max 2** rejections, finish the slice yourself and append a lesson to `docs/lessons.md` saying what the worker got wrong, so the next phase doc can mark that kind of slice non-delegable.

Scout reports get the lighter version. Collect each finding as `{"id","agent","claim","proposed_change","citation"}`, put the skill's apply-now criterion in `doctrine`, pipe to `python <delegate skill base dir>/scripts/jev-screen.py finding-triage`, and read findings in verdict order: `ASK` first (open questions for the user), then `REVIEW`, then `AUTO_APPLY`. Verify the citation of every `AUTO_APPLY` before applying; never auto-apply a finding whose `safe_to_auto_apply` is below 0.8, whatever its bucket. If the screen is skipped, apply the skill's own triage rubric unchanged.

## What the phase doc must carry

`/formalize-plan` writes a **Delegation** section next to **Autonomy & human-in-the-loop**: which sub-slices a worker may take and which the judge keeps, the allowed files per delegable slice, the test command per delegable slice, and the retry budget (default 2). A delegable slice without a file list or a test command is a plan defect; `/plan-audit`'s decomposition agent flags it. `/slash-goal` points at the section rather than restating it.

## Rules

1. **Cheap tier reads and implements; the session judges.** No exceptions for "small" judgments.
2. **Workers never commit, never touch plans or instruction files, never leave their slice.**
3. **Every worker diff goes through the check protocol.** Scope, tests you ran, screen, read all, decide.
4. **Jev orders and gates; it never excuses reading or applies anything.** Skipped screen means the prose rubric, not a free pass.
5. **Mark every dispatched prompt with `ROLE:<name>`** so `/tier-check` can prove the tier from transcripts.
6. **Two rejections, then the judge does it.** Log the lesson.

## What NOT to do

- Don't spawn Explore or a generic agent for reading when a scout exists; the generic one inherits the frontier model.
- Don't hand a worker a slice whose pass criterion it cannot run itself.
- Don't let a passing test output in a worker's report stand in for running it.
- Don't skip the read because the screen said low risk.
```

- [ ] **Step 4: Write `skills/tier-check/SKILL.md`**

```markdown
---
name: tier-check
description: Prove that delegation is real. Spawns a scout and a worker on a trivial task, then reads the runner's own transcripts to assert each ran on the cheap tier and the session on the frontier. Includes a negative control so the check is known to be able to fail. Run after installing the bundle, after changing agent definitions, or whenever a campaign's cost looks wrong.
allowed-tools: Agent, Read, Glob, Bash(python:*), Bash(date:*), Bash(powershell:*)
user-invocable: true
---

# Tier check

Delegation that is only declared is not delegation. This skill dispatches both cheap roles and then proves, from transcripts, which model each ran on.

## Step 1: Record the start time

Capture an ISO-8601 local timestamp before spawning anything (Bash: `date +%Y-%m-%dT%H:%M:%S`; PowerShell: `Get-Date -Format s`). Everything older is ignored.

## Step 2: Dispatch both roles

Spawn the two agents in one message so they run in parallel. Each prompt starts with its marker.

- **Claude Code**: `Agent` with `subagent_type: "scout"`, prompt `ROLE:scout Read README.md in the current directory and reply with its first heading only.` And `Agent` with `subagent_type: "worker"`, prompt `ROLE:worker Do not edit anything. Reply with the single word ok.`
- **Codex**: "spawn the `scout` agent with the prompt `ROLE:scout Read README.md and reply with its first heading only.`" and "spawn the `worker` agent with the prompt `ROLE:worker Do not edit anything. Reply with the single word ok.`"

Wait for both to return.

## Step 3: Assert from transcripts

Run the checker that ships with `/delegate` (path relative to that skill's base directory):

- Claude Code:
  `python <delegate base dir>/scripts/tier-check.py --runner claude --since <timestamp> --expect scout=claude-sonnet- --expect worker=claude-sonnet- --main claude-fable-`
- Codex:
  `python <delegate base dir>/scripts/tier-check.py --runner codex --since <timestamp> --expect scout=gpt-6-luna --expect worker=gpt-6-luna --main gpt-6-astra`

If your session model is not Fable / Astra, pass the prefix you actually run as `--main`. The checker exits 0 only when both roles have a fresh transcript on the expected prefix and the session is on the frontier prefix; missing evidence is a FAIL.

## Step 4: Negative control

Run the same command once more with a wrong expectation, e.g. `--expect scout=claude-opus-` (Codex: `--expect scout=gpt-6-sol`). It must exit 1 and name the model it actually saw. If it passes, the checker is not reading the transcripts you think it is: stop and report that instead of a green result.

## Step 5: Report

```
Tier check: <PASS | FAIL>
  scout   ran on <models>   expected <prefix>
  worker  ran on <models>   expected <prefix>
  main    ran on <models>   expected <prefix>
  negative control: <failed as required | DID NOT FAIL>
```

A PASS with a negative control that did not fail is reported as FAIL.

## Rules

- Never claim a tier from an agent's self-description. Only the transcript counts.
- The negative control is mandatory. A check that cannot fail is a false green.
- Do not edit the agent definitions from this skill; report and let the user decide.
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_doctrine.py -q`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/delegate/SKILL.md skills/tier-check/SKILL.md tests/test_doctrine.py
git commit -m "feat(delegate,tier-check): tiering doctrine and transcript-proven tier check"
```

---

### Task 6: Route existing skills through the doctrine

**Files:**
- Modify: `skills/audit/SKILL.md` (Step 3 at line 34-44, Step 4 at line 46-56)
- Modify: `skills/plan-audit/SKILL.md` (Step 3 at line 57-59 heading, Step 4 at line 81-91)
- Modify: `skills/slash-goal/SKILL.md` (default goal block at line 50-52, rails list at line 61, Rule 2 at line 70)
- Modify: `skills/formalize-plan/SKILL.md` (after the Autonomy paragraph, line 28)
- Modify: `skills/scaffold-project/templates/phase-template.md` (after `## Dependencies`)
- Modify: `skills/start-session/SKILL.md` (planning audit list, line 19-24)
- Modify: `skills/wrap/SKILL.md` (Step 3, line 43)
- Modify: `tests/test_doctrine.py` (append)

**Interfaces:**
- Consumes: the citation sentence and spawn phrasing from Task 5.

- [ ] **Step 1: Append the failing tests to `tests/test_doctrine.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_doctrine.py -q`
Expected: the 5 new tests fail; the 4 from Task 5 pass.

- [ ] **Step 3: Edit `skills/audit/SKILL.md`**

Replace the Step 3 heading and first paragraph:

```markdown
## Step 3: Spawn three scouts in parallel

Delegation follows `/delegate`: scouts read, workers implement inside their slice, the session judges, Jev screens. Send a single message with three Agent tool calls, each `subagent_type: "scout"` (Codex: spawn the `scout` agent three times), each prompt starting with `ROLE:scout`. Each agent gets a self-contained prompt: what changed, where to look, what to check, and the relevant instruction-file doctrine summary.
```

Replace the first two lines of Step 4 with:

```markdown
## Step 4: Screen, then synthesize and triage

Collect the three reports as findings `{"id","agent","claim","proposed_change","citation"}` and pipe them, with the apply-now criterion below as `doctrine`, to `python <delegate skill base dir>/scripts/jev-screen.py finding-triage`. Read in verdict order: `ASK`, then `REVIEW`, then `AUTO_APPLY`. Verify every citation before acting; never apply a finding whose `safe_to_auto_apply` is below 0.8. If the screen prints `skipped:`, use the ranking below unchanged.

Rank everything as:
```

In the "Important" list replace "Three parallel agents in ONE message" with "Three scouts in ONE message — never Explore or a generic agent, which inherit the session model".

- [ ] **Step 4: Edit `skills/plan-audit/SKILL.md`**

Replace the Step 3 heading and first paragraph:

```markdown
### Step 3: Spawn five scouts in parallel

Delegation follows `/delegate`: scouts read, workers implement inside their slice, the session judges, Jev screens. Send a single message with five Agent tool calls, each `subagent_type: "scout"` (Codex: spawn the `scout` agent five times), each prompt starting with `ROLE:scout`. Each agent gets a self-contained prompt: which plan to audit, what to check, the doctrine summary, and what shape the report should take.
```

Append to the decomposition agent's paragraph: "Also read the plan's **Delegation section**: flag any sub-slice marked delegable that lacks an allowed-files list or a test command, and flag a delegable slice whose pass criterion a worker cannot run itself."

Insert at the top of Step 4, before "Collect the five reports":

```markdown
Collect the five reports as findings `{"id","agent","claim","proposed_change","citation"}` and pipe them, with the derived-fix definition below as `doctrine`, to `python <delegate skill base dir>/scripts/jev-screen.py finding-triage`. Read in verdict order (`ASK`, `REVIEW`, `AUTO_APPLY`); `AUTO_APPLY` maps to the derived-fix bucket only after you verify the citation. If the screen prints `skipped:`, bucket by the rubric below unchanged.
```

Replace Rule 1 "Five parallel agents in ONE message." with "Five scouts in ONE message — never Explore, which inherits the session model."

- [ ] **Step 5: Edit `skills/slash-goal/SKILL.md`**

Replace the default goal block with (one line, `$` tokens space-flanked):

```
Complete <Phase N> from current HEAD. Open with $start-session and use docs/phases/<doc>.md as the contract with the latest devlog as current state. Do not start <next phase>. Execute end-to-end, proof-first, with focused tests and the phase's proof artifact. Delegate sub-slices per the doc's Delegation section and verify each per the delegate check protocol before closing it. Close each sub-slice with $wrap and run $audit then a final $end-session at phase end. Stage explicit paths only; no git add -A, no push. Never let a permission prompt stall the loop — use auto-approved command forms and, on denial, switch to an allowed equivalent and continue. Stop only for a real hard blocker.
```

Add to the non-negotiable rails sentence: ", delegation per the Delegation section with the check protocol,". Add to Rule 2's list: "delegation per the doc's Delegation section".

- [ ] **Step 6: Edit `skills/formalize-plan/SKILL.md`**

After the Autonomy paragraph (ends "A short `/slash-goal` then just points at this doc instead of re-encoding it.") insert:

```markdown
   **The Delegation section** decides what the cheap tier may build (doctrine: `/delegate`). For each sub-slice write: **delegable** or **judge-only**; for a delegable slice, the **allowed files** it may touch, the **test command** that proves its pass criterion, and the **retry budget** (default 2). Default delegable: any slice whose pass criterion is a test or an executing check the worker can run itself. Judge-only: anything touching the spec, instruction files, git, an unsettled decision, or a criterion that needs a human eye. A delegable slice without allowed files and a test command is a plan defect.
```

- [ ] **Step 7: Edit `skills/scaffold-project/templates/phase-template.md`**

After the `## Dependencies` block and before `## Success Criteria` insert:

```markdown
## Autonomy & human-in-the-loop

- Human-intervention points: __LIST__
- Gate tiers: self-serve __LIST__ / conditional-proceed __LIST__ / hard-stop __LIST__
- Pre-authorizations: __LIST__

## Delegation

| Sub-phase | Delegable? | Allowed files | Test command | Retry budget |
|-----------|------------|---------------|--------------|--------------|
| __N__a | delegable / judge-only | `path/one`, `path/two` | `__CMD__` | 2 |
| __N__b | delegable / judge-only | | | |
```

- [ ] **Step 8: Edit `skills/start-session/SKILL.md`**

Add a bullet to the planning-audit list after "Sub-phase decomposition exists…":

```markdown
- If the phase will run under a goal, the phase doc has a Delegation section naming which sub-slices a worker may take, their allowed files and test commands (doctrine: `/delegate`)
```

- [ ] **Step 9: Edit `skills/wrap/SKILL.md`**

Insert at the start of Step 3:

```markdown
If a worker implemented this slice, it reaches `/wrap` only after the `/delegate` check protocol: scope diff, tests you ran, screen, every hunk read, accepted.
```

- [ ] **Step 10: Run the whole suite**

Run: `python -m pytest tests -q`
Expected: all passed.

- [ ] **Step 11: Commit**

```bash
git add skills/audit/SKILL.md skills/plan-audit/SKILL.md skills/slash-goal/SKILL.md skills/formalize-plan/SKILL.md skills/scaffold-project/templates/phase-template.md skills/start-session/SKILL.md skills/wrap/SKILL.md tests/test_doctrine.py
git commit -m "feat(skills): route audits through scouts, workers through the check protocol, Delegation section in phase docs"
```

---

### Task 7: Docs in sync

**Files:**
- Modify: `README.md` (skill catalog table around line 100-125; workflow section line 161-173)
- Modify: `WORKFLOW.md` (after the `/plan-audit` section, line 83-91; and the `/slash-goal` section)
- Modify: `INSTALL.md` (Target paths table line 7-11; step 4-5 of manual install; Verifying list line 182-186; "What the installer does NOT touch" line 131-136)
- Modify: `AGENTS.md` (Repository structure table; Skills catalog; Conventions & doctrine)
- Modify: `tests/test_doctrine.py` (append)

- [ ] **Step 1: Append the failing tests**

```python
def test_docs_mention_delegate_and_tier_check(repo_root):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "`/delegate`" in readme and "`/tier-check`" in readme
    workflow = (repo_root / "WORKFLOW.md").read_text(encoding="utf-8")
    assert "scout" in workflow and "worker" in workflow and "check protocol" in workflow
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8")
    assert "<root>/agents/" in install and "CLAUDE_CODE_SUBAGENT_MODEL" in install and "default_subagent_model" in install
    agents_md = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "`agents/claude/`" in agents_md and "`skills/delegate/`" in agents_md and "/tier-check" in agents_md
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_doctrine.py -q -k docs`
Expected: 1 failure.

- [ ] **Step 3: Edit `README.md`**

Add two catalog rows in the session-management table:

```markdown
| `/delegate` | The model-tiering doctrine: cheap-tier `scout` agents read and report, cheap-tier `worker` agents implement one sub-slice each, the session judges, Jev screens each handoff. Other skills cite it. |
| `/tier-check` | Proves delegation is real: spawns a scout and a worker, then asserts from the runner's transcripts which model each ran on, with a mandatory negative control. |
```

Add to "How to use" after step 6: "Run `/tier-check` once after install so you know the cheap tier is actually being used."

- [ ] **Step 4: Edit `WORKFLOW.md`**

After the `/plan-audit` section add:

```markdown
### Model tiers (every stage)

The skills that spawn agents spawn cheap-tier **scouts** (Claude Code `sonnet`, Codex `gpt-6-luna`) to read and report; a slash-goal campaign hands delegable sub-slices to cheap-tier **workers** to implement. The session itself (Fable / Astra) is the only judge: it synthesizes scout reports, and it verifies every worker diff through the **check protocol** (scope diff, tests it ran itself, Jev diff-risk ordering, every hunk read, accept or re-dispatch, max two retries) before `/wrap`. Jev screens at each handoff so the judge reads the risky items first and never auto-applies a low-confidence finding. Doctrine in `/delegate`; proof in `/tier-check`.
```

In the `/slash-goal` section append: "The goal also points at the phase doc's Delegation section, which says which sub-slices a worker may take."

- [ ] **Step 5: Edit `INSTALL.md`**

Target paths table: add an "Agents directory" column with `-` for agent-neutral, `<root>/agents/` for Claude Code and Codex. Manual install: add step "Copy agents. `agents/claude/*.md` to `~/.claude/agents/`, `agents/codex/*.toml` to `~/.codex/agents/`. Same conflict rule as skills." Verifying: add "`<root>/agents/` has `scout` and `worker` for the claude and codex targets". Add a subsection:

```markdown
## Cheap-tier fallback (manual)

The installer prints these and never writes them. Add them so an agent spawned without a named role still lands on the cheap tier:

- Claude Code, `~/.claude/settings.json`: `"env": { "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet" }`
- Codex, `~/.codex/config.toml`: `[agents]` with `default_subagent_model = "gpt-6-luna"` and `default_subagent_reasoning_effort = "low"`

Then run `/tier-check` in each runner.
```

"What the installer does NOT touch": add `~/.codex/config.toml`.

- [ ] **Step 6: Edit `AGENTS.md`**

Repository structure table: add rows for `agents/claude/`, `agents/codex/`, `skills/delegate/` (with its two scripts), `tests/`. Skills catalog: add `/delegate`, `/tier-check` under session management. Conventions & doctrine: add

```markdown
- **Model tiers:** scouts read, workers implement one sub-slice, the session judges, Jev screens. The judge is never a subagent; workers never commit. Doctrine in `/delegate`, proof in `/tier-check`. Spawning Explore or a generic agent for reading is a defect: they inherit the session model.
```

Working ON the bundle: add "Run `python -m pytest tests -q` before every commit; it checks agent files, installers, helpers, and the doctrine strings skills must carry."

- [ ] **Step 7: Run the whole suite and commit**

Run: `python -m pytest tests -q`
Expected: all passed.

```bash
git add README.md WORKFLOW.md INSTALL.md AGENTS.md tests/test_doctrine.py
git commit -m "docs: model tiers, /delegate and /tier-check, agents install and cheap-tier fallback"
```

---

### Task 8: Live proof on this machine (judge runs this, not a worker)

**Files:** none created; deploys and runs.

- [ ] **Step 1: T1 install proof.** From the bundle root: `pwsh -NoProfile -File scripts/install.ps1 -Target all -DryRun -Overwrite` lists `agents/scout.md`, `agents/worker.md`, `agents/scout.toml`, `agents/worker.toml`. Then copy the new/changed skill folders (`delegate`, `tier-check`, `audit`, `plan-audit`, `slash-goal`, `formalize-plan`, `scaffold-project`, `start-session`, `wrap`) and the agent files directly to `~/.claude/skills`, `~/.agents/skills`, `~/.codex/skills`, `~/.claude/agents`, `~/.codex/agents` (never `-Overwrite` the world), then hash-compare each copied file against the bundle source.
- [ ] **Step 2: T2 + T4 on Claude Code.** Restart is needed for new agents to load; if the session cannot restart, dispatch with the Agent tool's `model: "sonnet"` per-call override AND `subagent_type` of the installed agent, and note which path was used. Run `/tier-check` per its SKILL.md, including the negative control. Record the PASS line and the negative-control FAIL line.
- [ ] **Step 3: T6.** `TYPESAFE_API_KEY= python skills/delegate/scripts/jev-screen.py diff-risk <<< '{"slice":{},"hunks":[]}'` prints `skipped`.
- [ ] **Step 4: T5 (Claude half) on example-skeleton.** Copy `example-skeleton` to the scratchpad, `git init` there (scrub `GIT_DIR`), dispatch a `worker` with `ROLE:worker`, slice "add a `## Delegation` table to `docs/phases/phase-1-mcp-foundation.md`", allowed files `docs/phases/phase-1-mcp-foundation.md`, test command `python -c "import sys;t=open('docs/phases/phase-1-mcp-foundation.md',encoding='utf-8').read();sys.exit(0 if '## Delegation' in t else 1)"`. Run the check protocol: `git diff --stat`, run the test command, `jev-screen.py diff-risk`, read the hunk, accept, commit with the slice's file only. Record the diff-risk output and the commit's file list.
- [ ] **Step 5: Hand-off for Codex.** Report to the user the exact `/tier-check` invocation to run in Astra (T3) and the T5 Codex half, and state plainly that those are not yet verified.

---

## Self-review

**Spec coverage.** Roles → Task 1, 5. Safety-net snippets → Task 2, 7. Branching map and check protocol → Task 5, 6. Jev screens (finding-triage, diff-risk) → Task 3; proof-altitude already shipped. Delegation section in phase docs → Task 6. `tier-check` → Task 4, 5. Installer → Task 2. Docs → Task 7. Tests T1–T6 → Task 2 (T1 unit), Task 3 (T6), Task 4 (T4 unit), Task 8 (T1, T2, T4, T5, T6 live; T3 handed off).

**Placeholders.** None: every code step carries its code; the template's `__X__` tokens are the template's own convention.

**Type consistency.** `read_frontmatter` defined in Task 1 conftest, used in Tasks 5–7. `jev-screen.py` exposes `build_questions`, `decide_finding`, `decide_diff`, `call_api`, `run`, matching the tests. `tier-check.py` exposes `scan_claude`, `scan_codex`, `evaluate`, matching the tests. Verdict strings `AUTO_APPLY | REVIEW | ASK` and status strings `meets_criterion | partial | off_scope | unclear` are identical in the helper, the doctrine, and the skill edits.
