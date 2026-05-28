---
name: end-session
description: End session - close devlog, run schema audit + lessons + state updates, optionally suggest slim or playbook extraction, commit.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(wc:*)
user-invocable: true
---

# End Session Skill

Wrap up the current session: close the devlog, audit frontmatter on touched files, update `docs/state.md`, capture any lessons learned, optionally surface slim / playbook nudges, and commit. Phase boundary if a sub-phase or full phase finished.

Multi-phase workflow. Each phase short. Skip silently if nothing to do.

## Phase 1: Read context

1. Glob `docs/devlogs/*.md` and find the most recent. Read it.
2. Read `docs/state.md` if it exists.
3. Read `AGENTS.md` and/or `CLAUDE.md` Current Status section.
4. Run `git status` and `git diff --stat` to see what changed this session.
5. Read the current phase doc from `docs/phases/` (most recent or referenced in state.md).

**Never ask whether to create a devlog.** Every `/end-session` produces a written record — that's the whole point of the skill. If the most recent devlog is `status: complete` (already closed by a prior `/end-session`), or no devlog exists at all for today's session, auto-create one now and proceed to Phase 2 to fill it.

Decide the file path based on what changed this session:

- **Code work** (git diff is non-empty, or files in this project were edited) → `docs/devlogs/YYYY-MM-DD-<topic>.md`. Derive `<topic>` from the primary files touched or the session's focus (e.g., `end-session-no-prompt-fix`).
- **No-code session** (research, info gathering, work that touched another project, conversation-only) → still write a record. Prefer `docs/devlogs/YYYY-MM-DD-<topic>-notes.md` so it's discoverable next session. If `docs/devlogs/` doesn't exist (project isn't scaffolded), fall back to `~/.claude/session-reports/YYYY-MM-DD-<topic>.md` (create the directory if needed).

Use the devlog frontmatter contract (`type: devlog`, `status: in-progress` on creation — Phase 2 flips it to `complete`, `session_start`, `session_end`, `phase`, `subphase`, `approval`, `summary`, `note_created`, `updated`). For no-code session reports written outside a scaffolded project, a lighter frontmatter is fine — at minimum `type: session-report`, `session_start`, `session_end`, `summary`, `note_created`. Synthesize body content from conversation history + git diff. Never pause to ask the user for any of these values.

## Phase 2: Devlog finalization

Walk the open devlog. Fill any empty / stub-level sections by synthesizing from `git status` + memory of the session:

- **Goal** — what the session aimed to accomplish (often pre-filled at start)
- **Work Done** — concrete things that happened
- **Decisions Made** — key calls, locks
- **Approvals & Locks** — anything explicitly signed off
- **Issues Encountered** — bugs, gotchas, surprises (used in Phase 5 for lessons.md)
- **Next Steps** — what tomorrow-self should pick up first
- **Cross-References** — wikilinks to phase docs, prior devlog, knowledge files

**Update frontmatter:**
- Set `session_end:` to current time (HH:MM, 24-hour). Capture when `/end-session` started, not a hypothetical end-time.
- Flip `status:` from `in-progress` to `complete`.
- Update `summary:` if stale.
- Update `updated:` to today.

Devlog is fully closed before continuing.

## Phase 3: Phase approval

If a sub-phase (e.g., 4a, 4b) or full phase was completed this session:

1. Set frontmatter `approval: approved` on the devlog.
2. Update the phase doc's frontmatter `status:` to `approved`.
3. Update `AGENTS.md` and `CLAUDE.md` Current Status sections, when present, to reflect the new active phase / sub-phase.
4. If the implementation plan's Phase Overview table tracks status, update the row.

If we paused mid-sub-phase, leave `approval: pending`. Don't update Current Status to a new phase.

## Phase 4: State update

If `docs/state.md` exists:

Walk the file. Update sections that shifted this session:
- Current focus
- Active sub-phase
- Blockers (appeared / cleared)
- Decisions pending
- Last devlog (link + status)

Set frontmatter `updated:` to today.

If no `docs/state.md` exists, skip silently. (It's optional.)

## Phase 5: Lessons check

**Never ask the user.** Auto-synthesize from this session's actual problems.

Scan the session for gotchas that took non-trivial effort to resolve. Signals:
- A bug, error, or failure that required more than one attempt to fix
- A surprising behavior, footgun, or non-obvious cause documented in the devlog's "Issues Encountered" section
- A workaround applied because the obvious approach didn't work
- Anything you'd want a future session to know before re-hitting the same wall

For each qualifying gotcha, append a new entry at the **top** of `docs/lessons.md`. Write the entry yourself from the session evidence — symptoms from what was observed, cause from the actual root cause found, fix from the actual change that worked. Cite `file:line` where relevant.

If nothing in the session qualifies, skip silently. Don't pad lessons.md with trivia.

```markdown
## YYYY-MM-DD — <Short title>

**Symptoms**: <what you saw>

**Cause**: <root cause, file:line if relevant>

**Fix**: <minimal change that worked>

**Frequency**: one-time | recurring | always

**Discovered**: YYYY-MM-DD
```

Update `lessons.md` frontmatter `updated:` to today.

If `docs/lessons.md` doesn't exist but qualifying gotchas were found, create it from the bundle's `lessons-template.md` and append the entries. Don't ask.

Skip silently if nothing memorable happened.

## Phase 6: Schema audit

Quick sweep on files modified this session (from `git status`). For each typed file (devlogs, phase docs, knowledge files, lessons, state, spec):

- Spot-check frontmatter parses as YAML
- Required fields present per type (see `docs/SCHEMA.md` if it exists)
- `summary:` containing `: ` (colon-space) is double-quoted
- Wikilinks resolve

**Surface anomalies in a list.** Don't auto-fix. Let the user decide whether to fix now or punt.

If `docs/SCHEMA.md` doesn't exist, the project hasn't adopted the frontmatter contract. Skip this phase (with a one-line note: "no SCHEMA.md found; skipping frontmatter audit").

## Phase 7: Slim suggestion

If `AGENTS.md` or `CLAUDE.md` crossed 25,000 characters during this session (compared to its size at the prior commit), suggest:

> AGENTS.md/CLAUDE.md is now N characters. Consider running the slimming workflow next session to extract reference content into knowledge files.

If either instruction file is over 40,000 characters, escalate the suggestion to a strong recommendation. Frame it as a workflow nudge.

If under 25,000, skip silently.

## Phase 8: Playbook nudge (every 5th approved phase)

Count how many devlogs in `docs/devlogs/` have `approval: approved` in frontmatter. If the count is a multiple of 5 (5, 10, 15, ...), and this session just produced an approval, prompt:

> You've shipped N approved phases. Anything from recent work that's cross-project shaped and worth extracting to a playbook? Run `/extract-playbook` if yes.

Skip silently otherwise. The frequency is configurable: read `playbook_nudge_every` from the active agent settings file in `.agents`, `.codex`, or `.claude` (default 5). Set to `0` to disable.

## Phase 9: Implementation plan verification

If a phase transition happened this session, verify `docs/implementation-plan.md` was updated. If not:

- Surface to user: "Implementation plan wasn't touched this session despite Phase X transitioning. Update before commit?"

Don't auto-edit. Wait for user direction.

## Phase 10: Commit

**Never stop here.** Always commit at the end of `/end-session`. A dirty tree with unrelated modified or untracked files is not a reason to halt — just don't stage them.

1. **Build the session-relevant file list.** This is the set the model touched during this session, sourced from:
   - Every file path passed to `Edit`, `Write`, or `NotebookEdit` during the session (the model already knows these from its own tool-call history — no shell command needed to recover them).
   - The devlog file finalized in Phase 2.
   - `docs/lessons.md` if Phase 5 appended to it.
   - `docs/state.md` if Phase 4 updated it.
   - The phase doc, `AGENTS.md`, `CLAUDE.md`, or implementation-plan.md if Phase 3 / 9 touched them.

   Any modified or untracked file NOT in this list is unrelated dirt — leave it alone. Do not stage it. Do not mention it as a blocker. Do not ask about it.

2. **Show what's changing** (relevant subset only): `git status --short -- <session-files>`, `git diff --stat -- <session-files>`, `git log --oneline -5`. If untracked session files exist, list them.

3. **Stage explicitly by path.** Never `git add -A` or `git add .`. Pass the session-relevant file list to `git add`. If the list is empty (no files touched, devlog already committed, etc.), skip staging and the commit — write only the final report.

4. **Synthesize commit message** from the devlog:
   - Subject (<=72 chars): from devlog `summary:` field, punchy
   - Body: 2-5 lines from Decisions Made + Approvals & Locks
   - Footer: include a co-author line only when the user or project convention requests one.

5. **Commit** via heredoc to preserve formatting:
   ```bash
   git commit -m "$(cat <<'EOF'
   <subject>

   <body>

   <optional co-author footer>
   EOF
   )"
   ```

6. **Push** if a remote is configured: `git push origin <current-branch>`. Verify with `git status` after.

7. Don't `--force`, don't `--amend`. If a hook fails, fix the underlying issue, re-stage, create a NEW commit.

## Final report

Concise summary:

```
Session wrapped — <duration>

Devlog:    docs/devlogs/<file>.md (status: complete, approval: <pending|approved>)
Files changed: <count>
Commits:   <count> new
Push:      <success | skipped | failed>

Phase status: <transitioned | unchanged>
Lessons: <added | none>
Schema audit: <clean | N anomalies>

Tomorrow's lead-in (from state.md current focus or devlog Next Steps):
"<short pull>"
```

## Rules

- **Always commit at the end.** `/end-session` is the commit gate for the session — show the relevant diff/stat in Phase 10, then commit without asking. An unrelated dirty tree is not a stop condition; just exclude those files from the stage list.
- **Stage only session-relevant files.** Files the model edited this session (plus devlog / lessons / state / phase doc / AGENTS / CLAUDE / implementation-plan if those phases ran). Leave the rest of the tree exactly as it was found.
- **Never `git push --force`** without explicit authorization.
- **Never `git add -A` or `git add .`.** Stage specific paths.
- **Never skip git hooks** with `--no-verify` unless user explicitly asks.
- **Devlog is sacred.** Never edit OLD devlog entries. Only the current one being closed.
- **Brevity over completeness.** If a phase has nothing to do, skip silently.
- **No conversation leaks in commit messages.** Write for git log readers, not the conversation.

## What NOT to Do

- Don't update Current Status unless a phase actually transitioned.
- Don't auto-fix schema audit findings. Surface, let user decide.
- Don't bump frontmatter `last_verified:` on knowledge files unless you actually verified.
- Don't ask the user for lessons content. Phase 5 auto-synthesizes from the session — if there's no real gotcha, skip the phase silently.
- Don't bundle the lessons append into the main commit. If lessons.md was touched, it gets folded into the same commit (single session = single commit).
