---
name: slash-goal
description: Author a completion-condition string for the "slash goal" command that drives as far as the user wants — often several phases or a whole overnight run — and stops only at genuinely irreversible forks. Sorts every gate into self-serve-and-continue, conditional-proceed, or hard-stop, elicits pre-authorizations up front so the loop doesn't stall at 2am, and returns the goal inline in chat. Run after /formalize-plan (and optional /plan-audit), before you start work.
allowed-tools: Read, Glob, Grep, AskUserQuestion, Bash(git log:*), Bash(git status:*)
user-invocable: true
---

# Slash Goal Skill

Author one **goal condition** for the `"slash goal"` command that drives the session as far as the user asks — a sub-phase, a phase, several phases, or a whole overnight run — and stops only when the work is genuinely done *or* it hits a fork that is genuinely irreversible or unsettled.

The whole craft of this skill is **gate handling**. An autonomous loop that stops at every sign-off, approval, and decision is useless overnight — it stalls at the first aesthetic gate and the user wakes to nothing. So the skill keeps the human in the loop the *right* way: at authoring time, not at runtime. It finds every gate across the span, sorts each into one of three tiers, and pre-clears as many as it safely can so the loop keeps moving and only stops for decisions that actually need a person and actually can't be undone.

This skill **returns the goal inline in the chat** (never writes it to a file) and does not run the command itself — `"slash goal"` is user-triggered.

## About the "slash goal" command

`"slash goal"` (written here with the word *slash* and no `/` character on purpose) is a built-in Claude Code command — requires Claude Code **v2.1.139 or later** — that sets a **completion condition** and then loops the agent's work autonomously until that condition is met. After every turn a small fast evaluator model checks the condition and returns a short reason for why it is or isn't satisfied; that reason steers the next turn. The goal persists across the session (and restores on `--resume`/`--continue`) until the condition is met, you run `"slash goal"` clear, or the session ends. Setting a new goal replaces the active one — no need to clear first.

Usage shape (paste, no leading `/` shown here for clarity):

- `"slash goal" <condition>` — set/replace the active goal; a turn starts immediately
- `"slash goal"` — view current goal status, turns, tokens, evaluator feedback
- `"slash goal" clear` — drop the active goal before completion

**The one constraint that shapes everything below:** the evaluator judges the condition **only against what the agent has surfaced in the conversation transcript.** It does not independently run commands or read files. So the condition must be written as things the agent's own output can *demonstrate* — and the generated goal must instruct the agent to surface its evidence (paste test output, MCP readbacks, screenshots, the commit hash, the devlog frontmatter) before the condition can read as met.

## When to use

- After `/formalize-plan` (and optional `/plan-audit`), before `/start-session`, when you want one or more phases to run under the `"slash goal"` loop instead of driving each sub-phase by hand.
- Especially for **long autonomous runs** ("get us far tonight," "drive the rest of the project") where stalling at a soft gate would waste the whole window.
- The plan has bounded sub-phases with pass criteria. If it's vague, tighten it first — a loose goal makes the evaluator either never stop or stop early.

## The gate tiers — the core idea

Before composing anything, every gate in the span gets sorted. A **gate** is any point the plan or the project convention would normally pause for a human. There are three kinds, and only one of them is an actual stop:

1. **Self-serve gate → run it yourself, log it, CONTINUE.** Anything the plan already frames as "automated check first, human only on mismatch" — aesthetic/visual sign-off via `vision_eval`, pixel cross-checks, panel-look reviews — *plus* the project's default per-sub-phase approval cadence. The goal converts these to: run the check, record the verdict + screenshot/evidence in the devlog, leave `approval: pending` for the human's morning review, and keep going. **Never a stop.**
2. **Conditional-proceed gate → pre-authorize with a testable condition.** A decision the loop would otherwise stop for, but which can be settled by a rule the loop can evaluate from its own output: "accept dependency D if `cargo deny` passes and its license is MIT/Apache — paste the output; else STOP"; "extending the already-vendored patch is fine (precedent D32) — do it and flag it; a core/upstream fork is not — STOP"; "you MAY draft spec amendments into `docs/spec-amendments-queued.md`, but never edit the spec itself." The skill **elicits the user's call on each of these up front** (or proposes a sensible default for one-line confirmation) and bakes the conditional-proceed into the goal text.
3. **Hard stop → STOP and report, with evidence.** Reserved for the genuinely irreversible or genuinely unsettled: git history rewrite (`git reset`, `git tag`, force-push), editing the spec contract, a core/upstream fork (a real maintenance commitment), a dependency that fails its pre-authorized condition, verification tools staying down *after* the semantic-only fallback was tried, a required cross-platform/parity leg being unreachable, the same check failing more than ~3 times, an irreversible action not pre-authorized, or any decision the plan does not settle. These are the **only** true stops.

The principle: **a stop is a last resort.** Every gate that can be self-served or conditionally pre-authorized must be, so an overnight run reaches as far as the plan safely allows instead of halting at the first sign-off. The human's judgment is spent at authoring time (tiers 1 and 2) so it doesn't have to be spent at 2am.

## Workflow

### Step 1: Scope the reach

Match the user's ask, don't default to a single gate-span. If they want one phase, scope to one phase. If they say "get us far tonight" or "drive the rest of the project," span **all** the phases they named — a multi-phase or whole-remaining-project goal is first-class here, not a deviation. Identify the phase doc(s) the span covers (argument, or the active/next phases in `docs/implementation-plan.md`).

### Step 2: Read context across the whole span

Read enough to know what "done" means, what proof the agent can surface, and where every gate sits:

1. Each phase doc in the span — sub-slice order (respect any non-obvious ordering, e.g. 4.1d before 4.1c), pass criteria, verification plan.
2. `docs/implementation-plan.md` — where the span sits and what's already done.
3. `docs/state.md` and `AGENTS.md` / `CLAUDE.md` Current Status — focus, blockers.
4. The project's session contract and **testability contract**: devlog location + frontmatter, the real `cargo`/test commands, and how features are proven (e.g. semantic MCP — write/invoke then read back `/sentinel/graph`, `/sentinel/ui`, `capture_frame` — with a documented semantic-only fallback when visual tools drop).
5. **Every gate and destructive step in the span**, with where each falls in the order.

### Step 3: Sort every gate into a tier

Walk the gates from Step 2 and classify each as **self-serve**, **conditional-proceed**, or **hard stop** per the definitions above. This is the analytic heart of the skill — get it right and the goal drives far without ever doing something unrecoverable.

### Step 4: Elicit pre-authorizations

For the conditional-proceed gates (and any soft gate where the project default is "wait for approval"), surface a short checklist to the user and get their call — propose a sensible default for each so they can clear it in one line. Use `AskUserQuestion` if it helps, or just present the list. Typical asks:

- "Self-serve all aesthetic/visual checks (vision_eval + screenshot logged, `approval: pending`) and continue? (recommended: yes)"
- "Commit each sub-slice `approval: pending` and roll on without per-sub-phase approval? (recommended: yes for overnight)"
- "Accept a new dependency automatically if `cargo deny` passes + license MIT/Apache, else stop? (recommended: yes)"
- "Extend an already-vendored patch freely but stop before any core/upstream fork? (recommended: yes)"
- "Draft spec amendments to a queue file but never touch the spec? (recommended: yes)"

If the user already pre-authorized these in conversation, use those answers — don't re-ask. Anything they decline becomes a hard stop instead.

### Step 5: Compose the goal condition

Write **one** condition string (capped ~4,000 chars), phrased as transcript-observable outcomes. **Reference the project's workflow commands with a `$` prefix, not a slash** (`$start-session`, `$audit`, `$end-session`) — that is the convention the runner expects, and a leading slash can be misread. (MCP paths like `/sentinel/graph` and shell commands keep their real syntax.) Include these parts:

1. **The span and order** — which phases/sub-slices, in the plan's implementation order; what's already done.
2. **DONE** — the measurable end state: every sub-slice's pass criterion met and PROVEN in-transcript, each recorded in a devlog and committed.
3. **Session bookends** — run `$start-session` ONCE at the start of the run to orient (last commit, latest devlog approval, `docs/state.md` if present), then drive autonomously; run a final `$end-session` at the very end before the completion report. These two commands must appear explicitly in the goal — orientation and close-out are not optional.
4. **Per-slice loop** — for each sub-slice: implement; verify against its pass criterion; PROVE via the testability contract (semantic MCP first, synthetic input where a human-gesture path must be exercised; paste green `cargo fmt --check` / `clippy -D warnings` / `cargo test`); write/append a devlog per the frontmatter contract; run `$audit` on the slice and fix every issue it surfaces before moving on (re-run the relevant proofs after fixes); close the slice like `$end-session` WITHOUT waiting for approval (devlog `status: complete`, `approval: pending`; update `docs/state.md` if it exists; commit ONLY related files with explicit `git add <paths>`); surface `git log -1` (subject+hash); roll straight to the next slice.
5. **Anti-stall / permission clause** — never let a tool-permission prompt freeze the loop. Instruct the agent to use only auto-approved command forms (`git add <explicit paths>`, `git commit`, `git status`, `git log`, `git diff`, the cargo checks, the MCP tools) and to never run a command that needs an approval prompt. If the harness denies a command, the agent must not sit waiting — switch to an allowed equivalent (e.g. stage explicit paths instead of `git add -A`) and continue; STOP only if no permitted path exists, naming the exact denied command. This is what keeps an overnight run from dying on a permission dialog.
6. **Self-serve clause** — run all aesthetic/visual checks yourself (vision_eval), save the screenshot path + verdict in the devlog, and CONTINUE; never stop for taste.
7. **Conditional-proceeds** — each pre-authorized decision as "do X when <testable condition> holds — paste the proof; otherwise STOP and report."
8. **Hard prohibitions** — never `git reset` / `git tag` / `git push --force` / `git add -A`; never edit the spec (may draft to the queue file only); never set `approval: approved`; never cross a genuinely irreversible gate.
9. **Stop-and-report list** — the tier-3 conditions: tools down after the semantic fallback, a failed pre-authorized condition, a core-fork need, an unreachable required parity leg, a check failing >3×, a `$audit` issue that can't be fixed without crossing a prohibition, an unauthorized irreversible action with no permitted alternative, or an unsettled decision. On any stop, surface exactly what's blocking and the evidence.
10. **Runtime cap + final report** — stop after N turns/hours and summarize; on full completion surface the final `git log`, every devlog path with its `status:`/`approval:` lines, and a phase-by-phase proof summary.

Keep it declarative. The condition describes the *end state, the tier rules, and the evidence* — the loop figures out the steps.

### Step 6: Return the goal inline

Print the goal **in the chat**, in a copy-paste block, then the command line. **Never write it to a file.**

```
Goal condition for "slash goal" (<span>):
─────────────────────────────────────────────
<the composed condition string>
─────────────────────────────────────────────

Run it (type the real slash command — pasting replaces any active goal):
"slash goal" <the same condition string>

(Requires Claude Code v2.1.139+. Check progress with a bare "slash goal";
cancel with "slash goal" clear.)
```

Then briefly: **what to expect** (the loop orients, drives the span surfacing proof, self-serves the soft gates, conditional-proceeds the pre-authorized ones, and stops only at the genuine forks — name them); **any human prerequisite** to do first; and, when the span is wide, **one honest caveat** that a multi-phase goal reaches farther but that the irreversible lines (git history, the spec, dependency acceptance, core forks) are kept as hard stops so "far" never means "unrecoverable."

## Rules

1. **A stop is a last resort.** Convert every gate you can — self-serve-and-continue or conditional-proceed. Reserve true stops for the irreversible or genuinely unsettled. An overnight goal that halts at the first aesthetic sign-off is a bug.
2. **Match the reach to the ask.** Single phase, several phases, or the whole remaining project — a wide multi-phase goal is first-class, not a deviation requiring an escape clause.
3. **Spend the human's judgment at authoring time.** Elicit the pre-authorizations up front (Step 4) so the loop doesn't stall on them at runtime.
4. **Self-serve aesthetics and the approval cadence.** Run the automated check, log verdict + evidence, `approval: pending`, continue. The human reviews logged notes later.
5. **Keep the irreversible lines hard.** Never author a goal that lets the loop rewrite git history, edit the spec, accept a dependency that fails its condition, or take an upstream fork. Those stay tier-3 stops.
6. **Prove in-transcript.** The evaluator only reads the conversation — bake in "paste the test output / MCP readback / screenshot / commit line / devlog frontmatter." Try the semantic-only fallback before declaring tools-down.
7. **A permission prompt must never halt the loop.** Every goal includes the anti-stall clause: use only auto-approved command forms, and on a denial switch to an allowed equivalent and continue rather than waiting. This is the single most common way an overnight run dies — bake it in every time.
8. **Always bookend with `$start-session` and `$end-session`.** Orientation at the start and close-out at the end are mandatory parts of the goal, plus a `$audit` per slice. Reference workflow commands with a `$` prefix, never a slash.
9. **Return the goal inline in chat — never a file.**
10. **Generate, don't run.** Produce the string and command line; the user runs it.
11. **Don't pad past the plan.** If a sub-slice has no pass criterion, say so and tighten the plan first.

## What NOT to do

- Don't stop at soft gates. Aesthetic sign-offs and the per-sub-phase approval cadence are self-served, not halts.
- Don't carve every gate out as a stop "to be safe" — that's the failure mode that strands an overnight run. Sort into tiers; stop only at tier 3.
- Don't silently pick a side on a real decision. Elicit the pre-authorization (or default + confirm); if declined, it's a hard stop.
- Don't author a goal that runs `git reset`/`git tag`/`git push --force`/`git add -A`, edits the spec, or self-approves.
- Don't author a goal that can stall on a permission prompt. Include the anti-stall clause and use only auto-approved command forms — a dialog at 2am ends the run.
- Don't omit the `$start-session` / `$end-session` bookends or the per-slice `$audit`. And don't prefix workflow commands with a slash — use `$`.
- Don't bury the goal in a file. It goes in the chat as copy-paste text.
- Don't run, simulate, or "test" the command — pasting it as text won't set a goal.
- Don't write a condition the agent's own output can't prove, and don't omit the runtime cap.
