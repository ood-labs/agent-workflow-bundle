---
name: wrap
description: Lightweight sub-phase close-out — a short devlog plus a commit, then move on. No phase ceremony (no lessons, schema audit, slim/playbook nudges, or Current Status changes). Use when a sub-slice is DONE and you want to roll straight to the next one. For mid-work saves use /checkpoint; for a real phase boundary use /end-session.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
user-invocable: true
---

# Wrap Skill

Close a finished sub-phase fast: write a short devlog, commit the work, move on. This is the middle weight of the three closers — heavier than `/checkpoint` (which is a mid-work save, not a boundary) and far lighter than `/end-session` (the full phase close-out). Reach for `/wrap` when a sub-slice meets its pass criterion and you want to roll straight to the next one without the 10-phase tax.

Do the whole thing in one quick pass. Don't synthesize a narrative; don't run any of the `/end-session` ceremony.

## Step 1: Short devlog

Find the most recent devlog in `docs/devlogs/`. If it's an `in-progress` entry for the sub-phase you're closing (e.g. a `/checkpoint` left it open), finalize that one. Otherwise create a new short entry `docs/devlogs/YYYY-MM-DD-<subphase-slug>.md`.

Keep it minimal — two short sections:

- **Done** — what shipped this slice and which pass criterion it met, with a one-line proof pointer (test name, commit, capture path).
- **Next** — one line on what the next slice picks up.

Frontmatter, nothing more:

```yaml
---
type: devlog
date: YYYY-MM-DD
phase: <N>
subphase: <e.g. 4.1b>
status: complete
approval: pending
summary: "<one line>"
---
```

`approval: pending` is deliberate — the human approves the **phase** later at `/end-session`, not each slice. Only add a Decisions/Issues note if something real happened; otherwise leave them out.

## Step 2: Mark done

Set the devlog `status: complete`, `approval: pending`. That's it. **Do not** touch `AGENTS.md` / `CLAUDE.md` Current Status, `docs/state.md`, the implementation plan, or the phase doc's status — those move at the real phase boundary in `/end-session`.

## Step 3: Commit

1. Stage only the paths touched this slice plus the devlog — explicit paths, **never** `git add -A` / `git add .`.
2. Short message from the devlog `summary:` (e.g. `feat(4.1b): <summary>`).
3. Commit. No push, no `--amend`, no tags.

## What this skill does NOT do

Skipped on purpose (that's the point — speed). All of these live in `/end-session`:

- Lessons synthesis (`docs/lessons.md`)
- Schema/frontmatter audit
- Slim suggestion, playbook nudge
- Implementation-plan verification
- Full `docs/state.md` walk
- Phase-approval ceremony / Current Status updates

If this slice actually finishes a whole **phase** (not just a sub-slice), don't use `/wrap` — run `/end-session` so the boundary is recorded properly.

## Rules

- **One sub-slice, one quick pass.** Short devlog, explicit-path commit, done.
- **Never `git add -A`/`.`; never push or amend.** Stage what you touched.
- **`approval: pending` always.** Slice close-out never approves; the phase boundary does.
- **No ceremony.** If you find yourself synthesizing lessons or auditing schema, you're in `/end-session` territory — stop.
- **Don't move the phase markers.** Current Status, state.md, plan status stay put until `/end-session`.
