---
name: formalize-plan
description: Formalize a plan into phase docs and implementation plan
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
user-invocable: true
---

We just finished planning (via plan mode or discussion). Now formalize it into the project's documentation system and commit.

DO:
1. **Read the plan file** from the active agent plan directory (check `.agents/plans/`, `.codex/plans/`, then `.claude/plans/`; use the most recently written one) to understand what was planned
2. **Create a detailed phase document** at `docs/phases/phase-{N}-{slug}.md` with:
   - Overview and motivation
   - Problem statement (before/after if applicable)
   - Deliverables table (ID, feature, tool, actions, status)
   - Each sub-phase with: parameters, response schemas, UE APIs, implementation details
   - Files summary (new files, modified files, no-change files with reasons)
   - Implementation order
   - Verification plan
   - Example agent workflow
   - Dependencies
3. **Update `docs/implementation-plan.md`**:
   - Add the new phase to the Phase Overview table with link to detailed plan
   - Add/update the phase section in the body (sub-phases table, MCP tools, dependencies, implementation order)
   - Update any "Future Phases" sections that referenced this phase as planned
4. **Update `AGENTS.md` and `CLAUDE.md`** Current Status sections when those files exist, so Codex and Claude Code see the same active phase
5. **Commit** all changes with message format: `docs(plan): Phase {N} - {Title}`

DON'T:
- Mark anything as complete or approved (this is planning, not implementation)
- Write any C++ or TypeScript code
- Modify any plugin or MCP server source files
