---
name: checkpoint
description: Checkpoint - devlog and commit without phase approval
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
user-invocable: true
---

Create a devlog entry for progress made so far and commit. This is NOT a phase completion - we're just saving progress mid-work.

DO NOT:
- Mark anything as "APPROVED"
- Treat this as a phase/subphase boundary
- Update AGENTS.md or CLAUDE.md "Current Status" to a new phase

DO:
- Write a devlog entry documenting what was accomplished
- Note what's still in progress or remaining for the current phase/subphase
- Commit with a descriptive message
- Capture any learnings in AGENTS.md or CLAUDE.md if we hit notable issues/solutions

This is a save point, not a milestone.
