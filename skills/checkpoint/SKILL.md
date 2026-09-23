---
name: checkpoint
description: Checkpoint - devlog and commit without phase approval
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(bd:*)
user-invocable: true
---

Create a devlog entry for progress made so far and commit. This is NOT a phase completion - we're just saving progress mid-work.

DO NOT:
- Mark anything as "APPROVED"
- Treat this as a phase/subphase boundary
- Update the AGENTS.md "Current Status" to a new phase

DO:
- Write a devlog entry documenting what was accomplished
- Note what's still in progress or remaining for the current phase/subphase
- Commit with a descriptive message
- Capture any learnings in AGENTS.md if we hit notable issues/solutions (never in a CLAUDE.md that is an `@AGENTS.md` import stub — AGENTS.md reaches both agents)

- Beads mirror (silent, only when the phase doc has `beads_epic`; doctrine `/beads-mirror`): **Progress** on the claimed row's bead (`bd note` + `bd heartbeat`, session `--actor`). Record it in the devlog's `beads:` line; never mention it to the user.

This is a save point, not a milestone.
