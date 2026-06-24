# Agent Workflow Bundle

A complete agent-driven development workflow for Codex, Claude Code, and other skill-aware coding agents. Hand this folder to an agent, run the installer, and it gets the same session-management skills, project bootstrap workflow, cross-project playbooks, and architectural patterns used across my software projects.

Everything is packaged as portable `SKILL.md` folders. Each skill is invocable by name in compatible agents; Claude Code can keep using slash-style names like `/<skill-name>`, and Codex can load the same folders from its skill home.

## What's inside

| Path | What it is |
|------|------------|
| `skills/` | User-invocable skills (session management, planning, knowledge tools, project bootstrap) |
| `skills/scaffold-project/templates/` | Frontmatter SCHEMA + 5 template files (devlog, phase, knowledge, lessons, state) used during scaffolding |
| `playbooks/` | Cross-project architectural patterns (MCP co-development, more accrete via `/extract-playbook`) |
| `playbooks/INDEX.md` | Master index of playbooks with keywords + applies_to |
| `example-skeleton/` | Minimal example of what `/scaffold-project` produces |
| `scripts/install.ps1` | Windows PowerShell installer for `.agents`, `.claude`, and/or `.codex` |
| `scripts/install.sh` | Portable macOS/Linux installer for `.agents`, `.claude`, and/or `.codex` |
| `scripts/install-macos.sh` / `scripts/install-linux.sh` | OS-named wrappers around `install.sh` |
| `INSTALL.md` | Agent-facing install instructions (skills + playbooks) |
| `WORKFLOW.md` | Full workflow narrative: conversation, research, spec, scaffold, develop, maintain |

## Skills

### Session management

These skills are intended to be user-invoked explicitly.

| Skill | Purpose |
|-------|---------|
| `/start-session` | Review last commit, read state.md, check most recent devlog frontmatter for `approval` status, audit next task plan, start work |
| `/checkpoint` | Save mid-work progress with devlog and commit, no phase approval |
| `/plan-audit` | Pre-implementation 3-agent audit (spec-alignment, toolchain-feasibility, sub-phase decomposition); applies a best-guess fix for every finding and flags the judgement calls to review/revert. Run after `/formalize-plan`, before starting work. |
| `/audit` | Post-implementation 3-agent quality gate (code, spec, test) with safe fixes applied |
| `/end-session` | Phase boundary: close devlog, schema audit, lessons prompt, state.md update, optional slim/playbook nudges, commit |
| `/find-session` | Inspect previous Claude Code or Codex session transcripts where supported |
| `/formalize-plan` | Turn a plan-mode plan into phase docs and implementation plan updates |
| `/slash-goal` | Author a completion-condition string for the built-in `"slash goal"` command that drives as far as you ask — one phase or a whole overnight run — and stops only at genuinely irreversible forks. Sorts every gate into self-serve-and-continue (aesthetics, approval cadence), conditional-proceed (pre-authorized decisions with a testable rule), or hard-stop (git history, spec edits, core forks, unsettled decisions); elicits the pre-authorizations up front so the loop never stalls at 2am; returns the goal inline in chat. Run after `/formalize-plan`, before starting work. |

### Planning, project bootstrap, knowledge

User-invocable. Agents may also auto-trigger when the description matches the conversation.

| Skill | Purpose |
|-------|---------|
| `/research-prompt` | Write a research-question document for deep external investigation (Gemini Deep Research, etc.) |
| `/spec-draft` | Generate `docs/design/spec.md` from research + conversation. Full mode (Sentinel-2 style, 15+ sections) or lite mode (8-10 sections). |
| `/scaffold-project` | Bootstrap a new project with full development system (AGENTS.md + CLAUDE.md, implementation plan, phase docs, knowledge base, code skeleton, MCP co-development surface for non-web apps) |
| `/slim-agent-md` | Refactor bloated AGENTS.md / CLAUDE.md files into knowledge files, lessons.md, or new skills. Hard ceiling 40K chars, target 20-25K. |
| `/slim-claude-md` | Backward-compatible alias for older Claude Code projects. |
| `/lookup` | Search project `docs/knowledge/` AND global playbooks by keyword |
| `/extract-playbook` | Distill cross-project content into the global playbook library |
| `/audit-playbooks` | Walk the playbook library, flag stale entries, optionally Explore-agent-verify against current docs |

## Playbooks

Cross-project architectural patterns that travel with your install under the active agent home, usually `~/.agents/playbooks/`, `~/.claude/playbooks/`, or `~/.codex/playbooks/`. Skills like `/lookup`, `/scaffold-project`, and `/audit-playbooks` read this library.

The bundle ships with one playbook out of the box (MCP co-development). The other 5 typical patterns (Windows distribution, TensorRT engine packaging, GPU/CUDA interop, ImGui/imnodes pitfalls, ZMQ IPC) accrete naturally as you run `/extract-playbook` from real projects.

A playbook is **cross-project**: it teaches a pattern that recurs across projects. Project-specific reference belongs in the project's `docs/knowledge/`, not here.

## Frontmatter contract

Every typed file in a scaffolded project (devlog, phase doc, knowledge file, lessons, state, spec, playbook) carries YAML frontmatter following `docs/SCHEMA.md`. This makes the discipline machine-checkable: `/start-session` greps `approval:` instead of pattern-matching free text, `/audit` checks phase status programmatically, `/find-session` filters by `status:` and `phase:`.

The bundle's `skills/scaffold-project/templates/SCHEMA.md` is the canonical contract. `/scaffold-project` copies it into every new project.

## How to install

Run one of the installer scripts from this folder:

```powershell
.\scripts\install.ps1 -Target all
```

```bash
chmod +x scripts/*.sh
./scripts/install.sh all
```

macOS and Linux wrappers are also included:

```bash
./scripts/install-macos.sh all
./scripts/install-linux.sh all
```

`all` installs to `~/.agents`, `~/.claude`, and `~/.codex`. Use `agents`, `claude`, or `codex` to install only one target. Existing files are not overwritten unless you pass `-Overwrite` in PowerShell or set `OVERWRITE=1` for Bash.

## How to use

See `WORKFLOW.md` for the full pipeline. The short version:

1. Have a long conversation with the agent about what you want to build.
2. `/research-prompt` to write investigation documents. Run them through Gemini Deep Research and save the findings.
3. Discuss findings with the agent.
4. `/spec-draft` to lock in architecture decisions in `docs/design/spec.md`.
5. `/scaffold-project` to create the project folder, plan, and code skeleton.
6. Open Codex or Claude Code in the new project. After `/formalize-plan` for each new phase, optionally `/plan-audit` before starting work.
7. Use `/start-session`, `/checkpoint`, `/audit`, `/end-session` to manage sessions. `/find-session` to inspect prior session transcripts.
8. As AGENTS.md or CLAUDE.md grows past 25K chars, run `/slim-agent-md`.
9. When you spot a recurring cross-project pattern, run `/extract-playbook`.

## When to use MCP co-development

For native, desktop, graphics, AI, or CLI applications, `/scaffold-project` recommends building a Rust MCP server alongside the main app from day one. Read `playbooks/mcp-co-development.md` for the full pattern.

For pure web apps, skip it. Browser DevTools and web-fetching tools usually give the agent enough visibility.

## Optional: Obsidian vault integration for playbooks

If you keep an Obsidian PKM vault (e.g., PXTCHWXRK), playbooks can live there with full Obsidian queryability. Set `playbooks_path` in the active agent settings file, such as `~/.agents/settings.json`, `~/.codex/settings.json`, or `~/.claude/settings.json`:

```json
{
  "playbooks_path": "/path/to/your/vault/01-lib/playbooks"
}
```

Skills detect at runtime. The bundle works fine without an Obsidian vault. With one, playbooks get wikilinks, tag queries, and dashboard surfacing.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
