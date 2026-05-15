---
name: audit
description: Audit current session's work in parallel (code / spec / test) and apply safe fixes
allowed-tools: Agent, Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet
user-invocable: true
---

Run a three-agent audit on the work done in this session: **code correctness / safety**, **spec + plan alignment**, and **test coverage**. Apply the safe fixes. Surface anything bigger before touching it.

This is a quality gate, not a phase boundary. Do NOT update AGENTS.md or CLAUDE.md "Current Status", do NOT mark anything APPROVED, do NOT commit unless asked. The audit's purpose is to catch bugs and gaps before /end-session locks the work in.

## Step 1: Scope what to audit

Find what changed since the last "approved" state on disk. In rough order of how much information they give:

1. `git status` — uncommitted changes (most likely the session's WIP).
2. `git log @{push}..HEAD --oneline` (or `git log origin/master..HEAD` if no upstream) — commits this session that haven't been pushed.
3. If both are empty: the most recent commit is fair game; the user invoked /audit on something they want a second look at.

Read the actual diffs so the audit prompts can be specific. Don't audit hypothetically.

## Step 2: Identify the doctrine to audit against

Look for whichever of these the project has, in this order:
- `docs/design/spec.md` (the canonical path written by `/spec-draft`), authoritative if present
- `docs/implementation-plan.md` or `docs/plan*.md` — the master roadmap
- `docs/phases/*.md` or `docs/phase-*.md` — current-phase pass criteria
- The most recent matching devlog in `docs/devlogs/` — what the session itself claims it did
- `AGENTS.md` and/or `CLAUDE.md` — project doctrine, universal rules, writing style, anti-patterns
- Any active plan in `.agents/plans/`, `.codex/plans/`, or `.claude/plans/` referenced from the instruction files

Skim each. The agent prompts will reference them by absolute path.

## Step 3: Spawn three Explore agents in parallel

Send a single message with three Agent tool calls (subagent_type=Explore). Each agent gets a self-contained prompt: what changed, where to look, what to check, and the relevant instruction-file doctrine summary.

**Code agent** — correctness, safety, resource lifetimes, Drop ordering, thread safety, error handling, edge cases, unsafe blocks, FFI invariants. Cite file:line. Categorize: ship-blocking / should-fix-now / nice-to-have. Explicitly call out things done RIGHT so the synthesis doesn't over-correct.

**Spec / plan agent** — does the work meet the stated claims? If `docs/design/spec.md` exists, it is the authority — measure work against the spec by section number (§X.Y). Are deviations documented and defensible? Are spec amendments needed? Writing style violations (instruction-file rules: no em dashes, no contrastive phrasing, no conversation leaks). Cross-doc consistency (AGENTS.md / CLAUDE.md / spec / implementation-plan / phase doc / devlog all telling the same story). **Phase coherence**: do the changes in the diff match the active phase doc's scope, or has scope crept? Cite the phase doc and the out-of-scope changes. **Devlog presence**: does a devlog exist for the current sub-phase? If not, flag.

**Test agent** — did the work ship with tests that would catch regressions? Bugs that "tests pass" glosses over? Test gaps that will bite the next phase? Concrete proposals: "add test X at file Y asserting Z." Distinguish coverage that's worth adding NOW from coverage that's better deferred to a later phase that has the right infrastructure.

Each agent should report under 800 words, ranked findings, file:line citations. Tell them to use WebFetch / WebSearch if a finding depends on external knowledge (e.g., "is this driver behavior documented?", "did this library API change in the latest release?").

## Step 4: Synthesize and triage

Collect the three reports. Rank everything as:

- **Ship-blocking**: bugs that make the work incorrect. Apply now.
- **Must-fix-now (regression-prevention)**: missing tests for a fixed bug; style violations the project enforces; plan-doc inconsistencies. Apply now.
- **Should-fix-now (small, safe)**: docstring fixes, minor refactors, missing error-context. Apply now.
- **Larger / risky / scope-expanding**: surface to the user. Don't touch without permission.
- **Defer to later phase**: capture in the devlog (if one exists) or as a note. Don't apply.

The "apply now" criterion: the change is small, mechanical, doesn't add new architecture, and doesn't require a design judgement the user hasn't made.

## Step 5: Apply the safe fixes

Use TaskCreate to track fixes if there are more than ~3 — otherwise just do them. After each fix, re-run whatever verification the project has (`cargo test` / `npm test` / etc.) to make sure nothing regressed.

Remove em dashes only when the project's instruction files explicitly forbid them (look for "no em dashes" or "em-dash" mentions in AGENTS.md or CLAUDE.md writing-style rules). Even then, only scan files modified this session, not pre-existing ones. Use `git diff` to disambiguate. If the project doesn't enforce a no-em-dash rule, skip the em-dash check entirely.

## Step 6: Document the audit (if a session devlog exists)

If `docs/devlogs/` has an entry from this session, append a "Post-landing audit + fixes" section matching the existing style of any prior audit sections in the repo (look for one). Capture:
- That three parallel agents audited (code / spec / test).
- Verdict: ship-blocking findings (count), fixes applied, items deferred.
- Each fix in 2-3 sentences: what, why, file path.
- Items considered and rejected (so future readers know they were thought about).

If no session devlog exists for the current work, treat that as a fix-now finding ("session work is not logged; instruction-file universal rule violated") and continue the audit. In the final report (Step 7), prompt the user whether to write one. Do NOT block the audit on this. Do NOT create a devlog file just for the audit; that's `/checkpoint` or `/end-session`'s job.

If a devlog exists but is in-progress (frontmatter `status: in-progress`), that's expected mid-session. Don't flag it.

## Step 7: Report back

Concise summary to the user:
- Audit verdict (passed / passed with fixes / blocked).
- Fixes applied (file:line bullets).
- Anything surfaced for user decision.
- Anything deferred and why.

Then stop. Do not commit. Do not run /end-session. Wait for the user's next move.

## Important

- This command runs whenever asked, including mid-session. It's not a phase gate.
- Three parallel agents in ONE message — do not serialize them.
- Trust the agents' verdicts but verify their proposed file:line citations before acting.
- If the work being audited is committed, fixes go into a NEW commit (or stay uncommitted for the user to bundle), never `--amend`.
- If the audit finds the work is fundamentally wrong, stop and surface immediately. Don't try to "fix" a wrong-architecture finding.
