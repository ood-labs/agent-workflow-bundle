---
name: slash-goal
description: Generate a completion-condition string for the "slash goal" command that drives a formalized phase to done — every sub-phase, the devlog, and the start/end-session steps — while keeping the human in the loop. Scopes each goal to a single human-gate span, carves out destructive/sign-off steps as stops, and returns the goal inline in chat. Run after /formalize-plan (and optional /plan-audit), before you start work.
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git status:*)
user-invocable: true
---

# Slash Goal Skill

Turn a freshly formalized phase plan into one **goal condition** you can hand to the `"slash goal"` command. The condition is written so the command's autonomous loop carries the session through a phase — every sub-phase, the devlog, and the start/end-session bookkeeping — and stops only when the work is genuinely done and committed, **or** the moment it reaches a step a human must own.

Because the loop is autonomous, the skill's real job is to draw the line between what the loop may do alone and what it must stop for. It scans the plan for destructive/irreversible actions and human gates (sign-off, approval, ratification, review), keeps those on the boundaries, and scopes each goal to a single gate-to-gate span — usually one phase, generated one at a time. A goal must never run a destructive step or self-clear a gate.

This skill **writes the goal string and returns it to you inline in the chat**. It does not run the command itself (`"slash goal"` is user-triggered), and it never writes the goal to a file — you read it from the conversation and paste it.

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
5. **Every destructive step and every human gate the plan names.** Read for: irreversible actions (`git reset`/history rewrite, force-push, tag moves, dropping data or schema, deleting files, anything the user confirmed once and wouldn't want re-run) and human-judgment gates (aesthetic/taste sign-off, approval, ratification, design decision, patch/security review). Note exactly where each falls in the sub-phase order — these set the goal's boundaries in Step 4.

### Step 3: Extract the verifiable end-state

From the reading, pull out, as a concrete list:

- **Sub-phases in order** (e.g. 4a → 4b → 4c) and the pass criterion for each.
- **The definition of done for this goal's span** — the single measurable state that means the bounded work is finished (its sub-phase criteria met, suite green, build exits 0, etc.).
- **The lifecycle steps the workflow requires around the code work** — orient at the start the way `/start-session` does (read last commit, devlog `approval`, state.md), write a devlog per the contract, and close out the way `/end-session` does (devlog `status: complete`, then `approval: pending` if a human gate still stands or `approval: approved` only when the human's sign-off is the trailing act — default to `pending` and let the human approve, state.md updated, committed).
- **Constraints that must hold** — files/areas that must NOT change, the frontmatter contract, "no unrelated files staged."

### Step 4: Scope the goal — one human-gate span at a time

A goal drives an *autonomous* loop, so anything a human must own has to fall on a boundary, never inside the loop. Using the gates and destructive steps found in Step 2, set the goal's scope:

- **Destructive / irreversible steps become human prerequisites — carved OUT of the goal.** The condition verifies the resulting state on turn 1 (e.g. "tree is at `<commit>`, file X present, file Y absent") and STOPS reporting "do `<step>` first" if it isn't met. The loop never performs the action itself.
- **Human gates become stop points.** The goal works up to the gate, surfaces the exact evidence the person needs to judge (screenshot, diff, readback, vision-eval), and STOPS without crossing it. The loop never self-approves, self-clears, or sets `approval: approved` to get past a gate.

These boundaries set the **unit of work**. Do **not** write one goal spanning a multi-phase arc when gates sit between the phases — bound each goal to a single gate-to-gate span (usually one phase, sometimes a shorter sub-phase run). Generate **one goal at a time**; the next is generated after the human clears the prior gate, so each gate stays a clean stop. Only when several phases carry no gate and no destructive step is a wider goal acceptable — and then say so explicitly rather than defaulting to it.

If the plan is missing, vague, or the gates are ambiguous, surface that and settle scope with the user before emitting a goal.

### Step 5: Compose the goal condition

Write **one** condition string (the command caps it at ~4,000 characters) with these parts, phrased throughout as transcript-observable outcomes:

1. **The measurable end state**, first and unambiguous. e.g. *"Phase 4.0 (sub-phases 4.0.2–4.0.4) is complete: every sub-phase pass criterion in `docs/phases/phase-4-*.md` is met and PROVEN, devlog written, work committed; then STOP."*
2. **The hard carve-outs** — list, up front, what the loop must never do: run each destructive prerequisite autonomously (verify its end-state on turn 1 and STOP if unmet instead), cross or self-clear a human gate, set `approval: approved`, touch the named off-limits files, or `git add -A`. These come from Steps 2 and 4 and are non-negotiable in the string.
3. **The lifecycle the loop must carry out** — work the sub-phases in order; for each, implement, verify against its pass criterion, and record it in the devlog; orient at the start and close out at the end the way `/start-session` and `/end-session` do (devlog `status: complete`, `approval: pending` unless the human's sign-off is the trailing act, `docs/state.md` updated, a commit made).
4. **The proof to surface** — because the evaluator only reads the transcript, require the agent to paste the evidence: the passing test/build output, the gate evidence a human needs (screenshot path, diff, readback, vision-eval), the final `git log -1` line (subject + hash), the devlog path with its `status:` and `approval:` frontmatter lines, and `git status` clean for session files.
5. **The human-in-the-loop stop condition** — bake in a standing instruction that the loop must STOP and report rather than guess or force through whenever it hits: an irreversible action not pre-authorized, an ambiguous decision the plan doesn't settle, a missing dependency / credential / tool, or the same check failing more than ~2–3 times. Human-in-the-loop is the default whenever the path is unclear. End with the named human gate the goal stops at (e.g. *"then STOP: BLOCKED ON HUMAN GATE — aesthetic sign-off; screenshot surfaced"*).
6. **A bounded runtime** — append a final stop valve, e.g. *"…or stop after 25–30 turns and report exactly what is blocking."*

Keep it tight and declarative. The condition describes the *end state, the carve-outs, and the evidence for it* — not a step-by-step script. The loop figures out the steps; the condition tells it where it must stop.

### Step 6: Return the goal inline

Print the goal **in the chat**, in a copy-paste block, then the exact command line. **Never write it to a file** — `.md` or otherwise — the user reads and pastes it from the conversation. Do **not** invoke the command yourself.

```
Goal condition for "slash goal" (Phase <N> — <span>):
─────────────────────────────────────────────
<the composed condition string>
─────────────────────────────────────────────

Run it (type the real slash command, not the quoted text):
"slash goal" <the same condition string>

(Requires Claude Code v2.1.139+. Check progress any time with a bare
"slash goal"; cancel with "slash goal" clear.)
```

Then, briefly:

- **What to expect** — the loop orients, refuses to proceed if a destructive prerequisite isn't done, works the span surfacing proof as it goes, and stops at the human gate (or the turn cap) without self-approving. You stay in control: a bare `"slash goal"` shows status, `"slash goal"` clear stops it.
- **Any human prerequisite** — if the goal carved one out (e.g. a confirmed reset), call it out as the one-time step to do first, and offer to walk the user through it.
- **Chaining** — note that this is one gate-bounded span; offer to generate the next goal once the current gate clears.

## Rules

1. **Generate, don't run.** The skill's job is to produce the condition string and the command line. The user runs the command.
2. **Return the goal inline in chat — never write it to a file.** The user reads and pastes it from the conversation. No `.md`, no scratch file.
3. **Keep humans on the boundaries.** Destructive/irreversible steps are carved-out prerequisites; human gates (sign-off, approval, ratification, review) are stop points. Neither ever happens inside the loop, and the goal must never self-approve or self-clear a gate.
4. **One goal per human-gate span; generate the next only after the prior gate clears.** Don't write a single goal across multiple gates or a whole multi-phase arc.
5. **Bake a human-in-the-loop stop into every goal.** The loop must stop and report — not guess or force through — on an irreversible/unauthorized action, an ambiguous decision the plan doesn't settle, a missing dependency, or a check failing repeatedly.
6. **Write every condition as transcript-observable.** The evaluator never runs commands or reads files — if the agent doesn't surface the proof, the goal can't read as met. Always bake "paste the test output / gate evidence / commit line / devlog frontmatter" into the condition.
7. **One measurable end state, stated first.** Anchor on the span's definition of done, not "make it good."
8. **Cover the full lifecycle, not just the code.** The goal must carry the start-of-session orientation, the per-sub-phase devlog entries, and the close-out (devlog complete, `approval: pending` by default, state.md, commit).
9. **Always include a stop valve.** A turn or time cap so a stuck loop ends and reports instead of spinning.
10. **Speak the project's contract.** Use its real test commands, devlog path, and frontmatter fields (`approval:`, `status:`) — read them in Step 2, don't assume.
11. **Don't pad past what the plan supports.** If the plan is vague or a sub-phase has no pass criterion, say so and tighten the plan first; don't paper over it with a fuzzy goal.

## What NOT to do

- Don't bury the goal in a file. It goes in the chat as copy-paste text.
- Don't write one goal spanning multiple human gates or a whole arc — scope to a single gate-to-gate span and generate the next after the gate clears.
- Don't let the loop perform a destructive step or cross a human gate. Those are prerequisites and stop points, not loop work.
- Don't default to `approval: approved`. Use `approval: pending` and let the human approve, unless their sign-off is genuinely the trailing act.
- Don't run, simulate, or "test" the `"slash goal"` command — you can't trigger it, and pasting it as text won't set a goal.
- Don't write a condition the agent's own output can't prove (e.g. "the code is clean" with no surfaced check).
- Don't omit the runtime cap — an unbounded condition that's subtly unsatisfiable loops until the session dies.
- Don't invent sub-phases or criteria the phase doc doesn't contain. Generate from the plan as written.
