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

`"slash goal"` (written here with the word *slash* and no `/` character on purpose) is a built-in Claude Code command — Claude Code **v2.1.139+** — that sets a **completion condition** and loops the agent's work autonomously until it's met. After each turn a small evaluator model checks the condition against **what the agent has surfaced in the transcript** (it does not run commands or read files itself) and returns a steer. Setting a new goal replaces the active one. View status with a bare `"slash goal"`; cancel with `"slash goal"` clear. Workflow commands inside the goal use `$` (Codex — the default) or `/` (Claude Code — only when the user asks for it); see Step 3 for the format rule.

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

Write a terse, doc-referencing condition — a few sentences, emitted as **one unbroken line** (no hard line breaks inside it). Default shape (Codex `$` form):

```
Complete <Phase N> from current HEAD. Open with $start-session and use docs/phases/<doc>.md as the contract with the latest devlog as current state. Do not start <next phase>. Execute end-to-end, proof-first, with focused tests and the phase's proof artifact. Close each sub-slice with $wrap and run $audit then a final $end-session at phase end. Stage explicit paths only; no git add -A, no push. Never let a permission prompt stall the loop — use auto-approved command forms and, on denial, switch to an allowed equivalent and continue. Stop only for a real hard blocker.
```

Drop anything the phase doc already states — don't re-encode sub-slice order, pass criteria, or the per-slice ritual, which the doc and the wrap command already own. The rails below stay regardless of length.

**Workflow-command syntax depends on the target runner:**

- **Default (unspecified) → Codex `$` form.** Write `$start-session`, `$wrap`, `$audit`, `$end-session`. In this form **every `$` token MUST be flanked by spaces** — never put a comma, period, semicolon, or any other character directly against it (`$wrap,` / `$audit.` / `$end-session;` won't parse). Phrase so each token is *followed by a space and a word* (`... with $wrap and run $audit then a final $end-session at phase end`), not by punctuation.
- **Claude Code (only when the user asks — e.g. "for claude", "claude format", "slashes") → `/` form.** Write `/start-session`, `/wrap`, `/audit`, `/end-session`. Punctuation adjacency is fine here (`/wrap;` parses).

The non-negotiable rails: open with the session-start command, the phase doc as the contract, "don't start the next phase," proof-first, per-slice close with the wrap command, audit + end-session at phase end, explicit-paths-only / no `git add -A` / no push, the anti-stall behavior, and "stop only for a real hard blocker."

### Step 4: Return the goal — and nothing else

Output **only** the goal, as a single unbroken line inside one fenced code block. No preamble, no "what to expect," no command-line line, no trailing commentary — nothing before or after the block. The block must contain **no internal line breaks** so it copies and pastes in one piece. **Never write it to a file** and never run the command yourself.

## Rules

1. **Keep the goal short — the phase doc is the contract.** Reference the doc; don't re-encode sub-slices, pass criteria, or gate detail that lives there. A goal that needs scrolling is a smell.
2. **Always keep the rails.** `$start-session`, the doc reference, "don't start the next phase," proof-first, per-slice `$wrap`, `$audit` + `$end-session` at phase end, explicit-paths-only / no `git add -A` / no push, anti-stall, and "stop only for a real hard blocker" stay in every goal regardless of length.
3. **A permission prompt must never halt the loop.** Auto-approved command forms only; on denial, switch to an allowed equivalent and continue. This is the most common way an overnight run dies.
4. **Gates are decided in the plan.** Self-serve / conditional-proceed / hard-stop and the pre-authorizations belong in the phase doc's Autonomy section; the goal just points there. If a decision is genuinely unsettled, surface it; otherwise make the call and proceed — don't interrogate the user.
5. **Match the reach to the ask.** Single phase or several — name the span and the stop line.
6. **Prove in-transcript — but transcript-observable is not the same as feature-proven.** The evaluator only reads the conversation, so the proof must be visible there (test output, MCP readback, screenshot, commit line, devlog frontmatter). The trap: a readback or a screenshot of placeholder text is transcript-observable and proves nothing. For a user-facing feature, the doc's proof method must *exercise the feature the way a user would* and **assert on captures** (vision_eval on what the image must contain), not just produce them. If the phase doc's pass criteria are all readback-shaped, that's a plan defect — surface it (it's what `/plan-audit`'s acceptance-bar agent catches), don't drive a goal that will clear a mock.
7. **Match workflow-command syntax to the target runner.** Default to Codex `$` form (`$start-session`, `$wrap`, `$audit`, `$end-session`) with **every `$` token flanked by spaces — never touching a comma, period, or semicolon**, or Codex won't parse it. Only when the user asks for Claude Code ("for claude", "slash format") use `/` form instead, where punctuation adjacency is fine. (MCP paths and shell commands keep their real syntax in both.)
8. **Output only the goal — one unbroken line, nothing else.** A single fenced block with no internal line breaks, no surrounding prose, no command line. Never a file. Generate, don't run.

## What NOT to do

- Don't write a long goal that duplicates the phase doc. If you're restating pass criteria or sub-slice order, stop — point at the doc instead.
- Don't drop the safety rails to make it short. Brevity comes from removing what the doc carries, not from removing `$start-session` / `$end-session` / anti-stall / the stop line.
- Don't author a goal that can stall on a permission prompt, runs `git add -A` / `git reset` / `git tag` / `git push --force`, edits the spec, or self-approves.
- Don't let a `$` workflow token touch punctuation in Codex form (`$wrap,` / `$audit.` break parsing) — keep a space on both sides. (In Claude `/` form this doesn't apply.)
- Don't wrap the goal across multiple lines or add any prose around it — one unbroken line, in one block, nothing else.
- Don't paper over a thin plan. Missing pass criteria or Autonomy section → fix the doc, don't inflate the goal.
- Don't run, simulate, or "test" the command.
- Don't add a turn/time cap. The goal stops at its hard blockers or when the work is done — never invent an arbitrary turn limit unless the user explicitly asks for one.
