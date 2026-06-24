---
name: slash-goal
description: Generate a completion-condition string for the "slash goal" command that drives an entire formalized phase to done — every sub-phase, the devlog, and the start/end-session steps. Run after /formalize-plan (and optional /plan-audit), before you start work.
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git status:*)
user-invocable: true
---

# Slash Goal Skill

Turn a freshly formalized phase plan into one **goal condition** you can hand to the `"slash goal"` command. The condition is written so the command's autonomous loop carries the session through the whole phase — every sub-phase, the devlog, and the start/end-session bookkeeping — and stops only when the phase is genuinely done and committed.

This skill **writes the goal string and hands it to you**. It does not run the command itself: `"slash goal"` is user-triggered, so the skill ends by printing the exact line for you to paste.

## About the "slash goal" command

`"slash goal"` (written here with the word *slash* and no `/` character on purpose) is a built-in Claude Code command — requires Claude Code **v2.1.139 or later** — that sets a **completion condition** and then loops the agent's work autonomously until that condition is met. After every turn a small fast evaluator model checks the condition and returns a short reason for why it is or isn't satisfied; that reason steers the next turn. The goal persists across the session (and restores on `--resume`/`--continue`) until the condition is met, you run `"slash goal"` clear, or the session ends.

Usage shape (paste, no leading `/` shown here for clarity):

- `"slash goal" <condition>` — set/replace the active goal; a turn starts immediately
- `"slash goal"` — view current goal status, turns, tokens, evaluator feedback
- `"slash goal" clear` — drop the active goal before completion

**The one constraint that shapes everything below:** the evaluator judges the condition **only against what the agent has surfaced in the conversation transcript.** It does not independently run commands or read files. So the condition must be written as things the agent's own output can *demonstrate* — and the generated goal must therefore instruct the agent to surface its evidence (paste test output, the commit hash, the devlog path, the `approval:` line) before the condition can read as met.

## When to use

- Right after `/formalize-plan` (and optional `/plan-audit`), before `/start-session`, when you want the phase to run end-to-end under the `"slash goal"` loop instead of driving each sub-phase by hand.
- The phase has a written plan with bounded sub-phases and pass criteria. If the plan is vague, stop and tighten it first — a loose goal makes the evaluator either never stop or stop early.
- Best for multi-sub-phase phases with a verifiable end state. A single 1-hour task doesn't need this.

## Workflow

### Step 1: Identify the plan

If the user gives an argument, treat it as a phase doc path or phase number. Otherwise find the most recently modified file in `docs/phases/` and confirm it's the phase to drive.

### Step 2: Read context

Read enough to know exactly what "done" means and what proof the agent will be able to surface:

1. The phase doc — sub-phase list, deliverables table, pass / definition-of-done criteria, verification plan.
2. `docs/implementation-plan.md` Phase Overview — where this phase sits, what comes before/after.
3. `docs/state.md` and the `AGENTS.md` / `CLAUDE.md` Current Status — current focus and any blockers.
4. The project's own session contract so the goal speaks its language: how devlogs are written and where (`docs/devlogs/`), the frontmatter contract (`docs/SCHEMA.md` if present — especially the `approval:` field), and the test / build commands the verification plan names.

### Step 3: Extract the verifiable end-state

From the reading, pull out, as a concrete list:

- **Sub-phases in order** (e.g. 4a → 4b → 4c) and the pass criterion for each.
- **The end-of-phase definition of done** — the single measurable state that means the whole phase is finished (all sub-phase criteria met, suite green, build exits 0, etc.).
- **The lifecycle steps the workflow requires around the code work** — orient at the start the way `/start-session` does (read last commit, devlog `approval`, state.md), write a devlog per the contract, and close out the way `/end-session` does (devlog `status: complete`, `approval: approved`, state.md updated, committed).
- **Constraints that must hold** — files/areas that must NOT change, the frontmatter contract, "no unrelated files staged."

### Step 4: Compose the goal condition

Write **one** condition string (the command caps it at ~4,000 characters) with these parts, phrased throughout as transcript-observable outcomes:

1. **The measurable end state**, first and unambiguous. e.g. *"Phase 4 (sub-phases 4a–4c) is complete: every sub-phase pass criterion in `docs/phases/phase-4-*.md` is met and `<test cmd>` exits 0."*
2. **The lifecycle the loop must carry out** — work the sub-phases in order; for each, implement, verify against its pass criterion, and record it in the devlog; orient at the start and close out at the end the way `/start-session` and `/end-session` do (devlog `status: complete`, `approval: approved`, `docs/state.md` updated, a commit made).
3. **The proof to surface** — because the evaluator only reads the transcript, require the agent to paste the evidence: the passing test/build output, the final `git log -1` line (subject + hash), the devlog path with its `status:` and `approval:` frontmatter lines, and the committed state of the working tree (`git status` clean for session files).
4. **Constraints that matter** — name what must not change and that only session-relevant files are staged (no `git add -A`).
5. **A bounded runtime** — append a stop valve so a stuck loop ends, e.g. *"…or stop after 25 turns and report what's blocking."*

Keep it tight and declarative. The condition describes the *end state and the evidence for it*, not a step-by-step script — the loop figures out the steps; the condition tells it when it's allowed to stop.

### Step 5: Hand it off

Output the goal in a single copy-paste block, then the exact command line to run. Do **not** invoke the command yourself.

```
Goal condition for "slash goal" (Phase <N>):
─────────────────────────────────────────────
<the composed condition string>
─────────────────────────────────────────────

Run it:  "slash goal" <the same condition string>

(Paste with the real command — type the slash, then `goal`, then the
condition. Requires Claude Code v2.1.139+. Check progress any time with
a bare "slash goal"; cancel with "slash goal" clear.)
```

Add two or three lines on what to expect: the loop will orient, work each sub-phase surfacing proof as it goes, and stop when the phase is committed and approved (or at the turn cap). Note that you stay in control — a bare `"slash goal"` shows status and `"slash goal"` clear stops it.

## Rules

1. **Generate, don't run.** The skill's job is to produce the condition string and the command line. The user runs the command.
2. **Write every condition as transcript-observable.** The evaluator never runs commands or reads files — if the agent doesn't surface the proof, the goal can't read as met. Always bake "paste the test output / commit line / devlog frontmatter" into the condition.
3. **One measurable end state, stated first.** Anchor on the phase's definition of done, not "make it good."
4. **Cover the full lifecycle, not just the code.** The goal must carry the start-of-session orientation, the per-sub-phase devlog entries, and the end-of-session close-out (devlog complete + approval, state.md, commit) — that's the whole point of generating it from a formalized plan.
5. **Always include a stop valve.** A turn or time cap so a stuck loop ends and reports instead of spinning.
6. **Speak the project's contract.** Use its real test commands, devlog path, and frontmatter fields (`approval:`, `status:`) — read them in Step 2, don't assume.
7. **Don't pad past what the plan supports.** If the plan is vague or a sub-phase has no pass criterion, say so and tighten the plan first; don't paper over it with a fuzzy goal.

## What NOT to do

- Don't run, simulate, or "test" the `"slash goal"` command — you can't trigger it, and pasting it as text won't set a goal.
- Don't write a condition the agent's own output can't prove (e.g. "the code is clean" with no surfaced check).
- Don't omit the runtime cap — an unbounded condition that's subtly unsatisfiable loops until the session dies.
- Don't invent sub-phases or criteria the phase doc doesn't contain. Generate from the plan as written.
