# Agent Workflow Bundle — Agent Instructions

**Canonical instructions live in [CLAUDE.md](CLAUDE.md). Edit that file, not this one.** AGENTS.md mirrors CLAUDE.md (a symlink to it on the maintainer's machines; a thin pointer in the repo because Git for Windows has `core.symlinks=false`). Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md` — both resolve to the same content.

For everything — what this project is, the workflow walkthrough and its visual graph, the skills catalog, deploy discipline, and the settled conventions — see **[CLAUDE.md](CLAUDE.md)**.

## One thing you must not miss

- **`skills/` is the source of truth**, but editing a skill does nothing until you deploy it. Local deploy target is **`~/.claude/skills/`** only — `~/.agents/skills/` is symlinked to it (and `.agents` is what Codex reads), so one copy covers both agents. Remote machines in use: e.g. sbot2 at `\\sbot-2\C\Users\bot\.claude\skills\`. Target agents must restart to reload.
