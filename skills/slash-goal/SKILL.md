---
name: slash-goal
description: Author a SHORT completion-condition for the "slash goal" command that points at the phase doc as the contract and drives it end-to-end — proof-first, bookended by $start-session / $audit / $end-session, stopping only at genuine hard blockers. The phase doc (its pass criteria + Autonomy section) carries the detail; the goal stays terse. Run after /formalize-plan (and optional /plan-audit), before you start work.
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git status:*)
user-invocable: true
---

# Slash Goal Skill

Author one **short** `"slash goal"` condition that names a phase, points at its phase doc as the contract, and turns the loop loose to execute it end-to-end. The detail — sub-slice order, pass criteria, proof method, and which human gates are pre-cleared — lives in the **phase doc**, not in the goal string. A good goal is a few sentences: *which* phase, *where* the contract is, the standing safety rails, and where to stop. Everything else is read from the doc at runtime.

The division of labor:

- **The phase doc is the contract.** `/formalize-plan` writes it with pass criteria and an **Autonomy & human-in-the-loop** section that marks where a person is genuinely needed, batches those points, and records the pre-authorized decisions (the gate tiers below). The loop reads it each slice.
- **The goal is a thin pointer.** It references the doc, sets the `$start-session` / `$audit` / `$end-session` bookends and the safety rails, and bounds the run. It does **not** re-encode the plan.

If the phase doc lacks pass criteria or an Autonomy section, that's a plan gap. Fix it in the doc (or, only if the user wants a stopgap, fold the missing pre-authorizations into the goal) rather than papering over it with a wall-of-text goal.

## About the "slash goal" command

`"slash goal"` (written here with the word *slash* and no `/` character on purpose) is a built-in Claude Code command — Claude Code **v2.1.139+** — that sets a **completion condition** and loops the agent's work autonomously until it's met. After each turn a small evaluator model checks the condition against **what the agent has surfaced in the transcript** (it does not run commands or read files itself) and returns a steer. Setting a new goal replaces the active one. View status with a bare `"slash goal"`; cancel with `"slash goal"` clear. On a runner that uses `$` for workflow commands (Codex-style), the goal still references `$start-session` etc. with `$`, never a slash.

## Gates live in the plan, not the goal

Every place a human might pause is a **gate**, sorted into three tiers — decided at plan time and recorded in the phase doc's Autonomy section:

1. **Self-serve** (aesthetic/visual checks, the per-sub-phase approval cadence) — the loop runs the check, logs the verdict + screenshot in the devlog, commits `approval: pending`, and **continues**. Never a stop.
2. **Conditional-proceed** — a real decision pre-authorized with a testable rule the loop can evaluate from its own output ("accept the dep if `cargo deny` passes and the license is MIT/Apache, else stop").
3. **Hard stop** — the genuinely irreversible or unsettled (git history rewrite, editing the spec, a core/upstream fork, a failed pre-authorized condition, tools down after the semantic fallback, an unsettled decision). The only real stops.

The goal does not restate all this — it says *"follow the doc's Autonomy section; stop only for its hard blockers."* The human's judgment is spent once, at plan time.

## Workflow

### Step 1: Identify the phase and reach

Match the user's ask. One phase, several phases, or the rest of the project — a multi-phase goal is fine; just name the span and the phase doc(s). Identify the **next** phase that must NOT be started (the stop line).

### Step 2: Confirm the phase doc can carry the goal

Read the phase doc (and `docs/implementation-plan.md` current edge, latest devlog). Verify it has: bounded sub-slices with **pass criteria**, the **proof method / testability contract**, and an **Autonomy & human-in-the-loop** section with the gate tiers + pre-authorizations. If any is missing:

- Prefer to fix the **doc** (or tell the user it needs `/formalize-plan` to add the Autonomy section).
- If the user already pre-authorized decisions in conversation that the doc doesn't carry, either add them to the doc or, as a stopgap, inline just those one-liners in the goal. Only surface a decision to the user if it's genuinely unsettled and you can't derive it — otherwise make the call, note it, and move on. Don't interrogate the user to author a goal.

### Step 3: Emit the short goal

Write a terse, doc-referencing condition — a few sentences. Default shape:

```
Complete <Phase N> from current HEAD. Start with $start-session. Use
docs/phases/<doc>.md as the contract and the latest devlog as current
state. Do not start <next phase>. Execute end-to-end, proof-first, with
focused tests and the phase's proof artifact, then $audit and
$end-session. Stage explicit paths only; no git add -A, no push. Never
let a permission prompt stall the loop — use auto-approved command forms
and, on denial, switch to an allowed equivalent and continue. Stop only
for a real hard blocker.
```

Drop anything the phase doc already states — don't re-encode sub-slice order, pass criteria, or the per-slice ritual ($audit/devlog/approval), which the doc and $end-session already own. The rails below stay regardless of length.

The non-negotiable rails: `$start-session` to open, the phase doc as the contract, "don't start the next phase," proof-first + `$audit` + `$end-session`, explicit-paths-only / no `git add -A` / no push, the anti-stall behavior, and "stop only for a real hard blocker."

### Step 4: Return the goal inline

Print the goal **in the chat**, in a copy-paste block, then the command line. **Never write it to a file.** Add one or two lines on what to expect and which hard blockers could stop it. Don't run the command yourself.

## Rules

1. **Keep the goal short — the phase doc is the contract.** Reference the doc; don't re-encode sub-slices, pass criteria, or gate detail that lives there. A goal that needs scrolling is a smell.
2. **Always keep the rails.** `$start-session`, the doc reference, "don't start the next phase," proof-first + `$audit` + `$end-session`, explicit-paths-only / no `git add -A` / no push, anti-stall, and "stop only for a real hard blocker" stay in every goal regardless of length.
3. **A permission prompt must never halt the loop.** Auto-approved command forms only; on denial, switch to an allowed equivalent and continue. This is the most common way an overnight run dies.
4. **Gates are decided in the plan.** Self-serve / conditional-proceed / hard-stop and the pre-authorizations belong in the phase doc's Autonomy section; the goal just points there. If a decision is genuinely unsettled, surface it; otherwise make the call and proceed — don't interrogate the user.
5. **Match the reach to the ask.** Single phase or several — name the span and the stop line.
6. **Prove in-transcript.** The evaluator only reads the conversation; the doc's proof method must produce transcript-visible evidence (test output, MCP readback, screenshot, commit line, devlog frontmatter).
7. **Use `$` for workflow commands, never a slash.** `$start-session`, `$audit`, `$end-session`. (MCP paths and shell commands keep their real syntax.)
8. **Return the goal inline in chat — never a file. Generate, don't run.**

## What NOT to do

- Don't write a long goal that duplicates the phase doc. If you're restating pass criteria or sub-slice order, stop — point at the doc instead.
- Don't drop the safety rails to make it short. Brevity comes from removing what the doc carries, not from removing `$start-session` / `$end-session` / anti-stall / the stop line.
- Don't author a goal that can stall on a permission prompt, runs `git add -A` / `git reset` / `git tag` / `git push --force`, edits the spec, or self-approves.
- Don't prefix workflow commands with a slash — use `$`.
- Don't paper over a thin plan. Missing pass criteria or Autonomy section → fix the doc, don't inflate the goal.
- Don't run, simulate, or "test" the command.
- Don't add a turn/time cap. The goal stops at its hard blockers or when the work is done — never invent an arbitrary turn limit unless the user explicitly asks for one.
