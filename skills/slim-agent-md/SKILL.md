---
name: slim-agent-md
description: Refactor bloated AGENTS.md or CLAUDE.md files into lean primary instructions plus topic-grouped knowledge files. Agent-neutral alias for slim-claude-md.
user-invocable: true
---

# Slim Agent Instructions Skill

Use the same workflow as `slim-claude-md`, but treat `AGENTS.md` as the primary cross-agent instruction file and `CLAUDE.md` as the Claude Code compatibility file.

Read `../slim-claude-md/SKILL.md` from this bundle when available. If the installed agent cannot resolve that relative path, follow these rules:

1. Read `AGENTS.md` and `CLAUDE.md` when present.
2. If both files are under 25,000 characters, report counts and stop.
3. Move detailed reference material to `docs/knowledge/` with frontmatter.
4. Move workflow-shaped procedures to `.agents/skills/<name>/SKILL.md`, mirroring to `.codex/skills/` or `.claude/skills/` only when the active agent needs it.
5. Keep the instruction files lean, preserve section order, and leave pointers to extracted knowledge.
