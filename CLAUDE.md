# Claude Code Instructions — Agent Workflow Bundle

Canonical cross-agent instructions live in [AGENTS.md](AGENTS.md). This file is a Claude Code compatibility pointer — read AGENTS.md for the full picture, and keep the two in sync when Claude-specific behavior diverges.

## TL;DR for working on this repo

- This is the **Agent Workflow Bundle**: a portable set of `skills/` + `playbooks/` + an installer that other projects install. There's no app to build — the product is the prose in each `skills/<name>/SKILL.md`.
- `skills/` is the **source of truth**. Editing a skill does nothing until you deploy it to the install roots (`~/.agents`, `~/.claude`, `~/.codex`) and any machine in use (e.g. sbot2 via `\\sbot-2\C\Users\bot\.claude\skills\`). Target agents must restart to reload.
- The installer is **all-or-nothing on conflicts** — to update one skill, copy that single folder; don't `-Overwrite` everything.
- When a skill changes, update `README.md`, `WORKFLOW.md`, and `INSTALL.md` in the same commit.
- The workflow walkthrough and a visual graph of it are in [AGENTS.md](AGENTS.md#the-workflow-this-bundle-implements); the full narrative is [WORKFLOW.md](WORKFLOW.md).

## Conventions (see AGENTS.md for the full list)

No interactive prompts in skills · `/end-session` always commits touched files only · goals are thin pointers to the phase doc · `$`-prefixed workflow commands in goal text · anti-stall on permission prompts · tiered human-in-the-loop · proof-altitude (a feature criterion must be false unless the experience exists). Conventional commits; never `git add -A` or `--force`; commit/push only when asked.
