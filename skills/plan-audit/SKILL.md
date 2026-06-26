---
name: plan-audit
description: Pre-implementation four-agent audit on a phase plan (spec-alignment, acceptance-bar/proof-altitude, toolchain-feasibility, sub-phase decomposition). Run after /formalize-plan, before starting work. Catches plan-level issues before code is written — including pass criteria a mock could satisfy — and applies a best-guess fix to the plan doc for every finding, flagging the judgement calls for you to review or revert.
allowed-tools: Agent, Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch
user-invocable: true
---

# Plan Audit Skill

Run a four-agent audit on a phase plan BEFORE implementation begins. Catches gaps, pass criteria a mock could clear, infeasible toolchain assumptions, and bad sub-phase decomposition while they're cheap to fix — then **applies a best-guess fix to the plan doc for every finding it can** and reports what it did, the same hands-off way `/audit` fixes code. The user reviews the judgement calls after, instead of being asked up front.

This is the pre-implementation counterpart to `/audit` (which runs after work is done). Same agent infrastructure, same apply-then-report behavior, different inputs and prompts.

## When to Use

- After `/formalize-plan`, before starting work on the phase
- When the plan involves new libraries, SDKs, or APIs you haven't used before
- When the phase will span more than one sitting (multi-week effort)
- When you suspect the plan is incomplete or hand-wavy
- User says "audit the plan", "review the plan", "check the plan before I start"

## Workflow

### Step 1: Identify the plan

If the user provides an argument, treat it as a phase doc path or phase number.

If no argument, find the most recently modified file in `docs/phases/`. Confirm with user before proceeding.

### Step 2: Read context

Read in order:
1. The phase doc itself
2. `docs/design/spec.md` if present (authoritative spec)
3. `docs/research_results/` files relevant to the phase topic
4. `docs/research_prompts/` files relevant to the phase topic
5. `docs/implementation-plan.md` Phase Overview table for prior + later phases
6. `AGENTS.md` and/or `CLAUDE.md` for project doctrine
7. Recent devlogs from the prior phase (the just-shipped work informs what's realistic next)

### Step 3: Spawn four Explore agents in parallel

Send a single message with four Agent tool calls (`subagent_type=Explore`). Each agent gets a self-contained prompt: which plan to audit, what to check, the doctrine summary, and what shape the report should take.

**Spec-alignment agent**: does the plan deliver what the spec, research, and prior conversation say is needed — and are the pass criteria as strong as the spec? Trace each major deliverable back to a spec section, research finding, or design decision. Flag features with no traceability and spec areas the plan should cover but doesn't. Then go further: for the spec section the plan names as **governing**, check that each requirement in it maps to an enforceable pass criterion. Citing a spec is not verifying against it — flag any place where a pass criterion could pass while the governing spec requirement stays unmet (the phase doc has become a lower bar than the spec it cites). Cite §X.Y.

**Acceptance-bar / proof-altitude agent**: could a mock satisfy this plan? For each sub-phase's pass criterion ask: *could a model-only, stubbed, or placeholder build clear it?* Criteria are too low when they measure a proxy layer (MCP/readback returns the right JSON, a log line, an artifact file exists, a screenshot was captured) instead of the layer where the feature's value lives (a human can SEE the thing, can DO the action, or it EXECUTES and the output changes). Specifically flag: (1) any user-facing feature with no criterion that is **false unless the experience exists** — at least one visible/behavioral/executing gate is mandatory; (2) "screenshot proof" with no assertion on what the image must contain (require a vision_eval-style content assertion); (3) features whose only evidence is readback; (4) a phase that delivers only substrate (a "Model", "Boundary", or "foundation" phase) without saying plainly that it delivers nothing visible or executable yet, and without a named companion phase for the user-facing/executing part — so "substrate done" can't be reported as "feature done." This is the check that catches a green-all-proofs build that's a placeholder the moment you open it.

**Toolchain-feasibility agent**: do the libraries, APIs, SDKs, and tools the plan assumes exist and behave as the plan assumes? Check version compatibility against current platform support matrices. Check recent API changes (breaking changes in the last 6-12 months). Check whether real-world performance numbers in the plan are achievable (search for benchmarks, GitHub issues, vendor docs). Use WebFetch/WebSearch when the plan rests on a vendor claim. Flag any "this should work" that isn't backed by evidence.

**Sub-phase decomposition agent**: is the work decomposed so each sub-phase can be verified independently? Are dependencies between sub-phases explicit? Hidden ordering constraints? Is each sub-phase shippable in 1-2 sittings (1-3 days work)? Flag mega-phases (>1 week of work) that should be split. Flag dependencies that aren't named. Flag sub-phases without pass criteria.

Each agent reports under 800 words, ranked findings, file:line citations where relevant.

### Step 4: Synthesize and triage

Collect the four reports. The default is **resolve everything you can** — apply a best-guess fix to the phase doc for every finding, then report what you did so the user can revert. Sort each finding into one of three buckets:

- **Derived fix**: mechanical, unambiguous revision (missing pass criteria, unnamed dependency, missing `§X.Y` traceability, wrong library/version the toolchain agent corrected with evidence, obvious mega-phase seam). Apply it. No flag needed beyond listing it.
- **Judgement-call fix**: resolving it took a choice you made on the user's behalf — dropping a deliverable with no spec traceability, picking a replacement library for a deprecated one, adding a new sub-phase to cover a spec gap, restructuring the decomposition. Apply your best-guess resolution anyway, but **flag it in the report as a judgement call** with the alternative you didn't take, so the user can revert or redirect in one step.
- **Genuinely unresolvable**: you cannot make a defensible best guess because the needed information doesn't exist in the spec, research, conversation, or codebase (e.g. "which of two equally-valid architectures does the user want?" with no signal either way). Leave the plan as-is for this point and surface it as an open question. This bucket should be small — only use it when guessing would be reckless, not merely when a choice exists.

Also keep a **Considered but accepted** list for findings you reviewed and deemed fine (no change).

When you *can* make a reasonable best guess, make it and flag it — don't punt to the user. Only the genuinely-unresolvable bucket stays unfixed.

### Step 5: Apply the fixes

Edit the phase doc directly to resolve every derived fix and judgement-call fix. If there are more than ~3, track them with a quick checklist as you go. Preserve the doc's existing structure and writing style (match heading levels, list style, and the project's instruction-file rules — e.g. no em dashes if the project forbids them).

For judgement-call fixes, write the resolution into the plan as if it were decided, but keep a precise note of what you changed and the alternative, for the report and the audit section. The user must be able to revert any single judgement call without unpicking the others.

After editing, re-read the affected sections to confirm the plan still reads coherently — no dangling references, no sub-phase numbering gaps, no contradiction with a section you didn't touch.

Do NOT write code. Do NOT commit. This skill revises the plan only.

### Step 6: Document the audit in the phase doc

Append (or update) a "Plan audit findings" section at the end of the phase doc capturing:
- That four parallel agents audited (spec-alignment / acceptance-bar / toolchain-feasibility / decomposition).
- Verdict and counts: derived fixes applied, judgement-call fixes applied, open questions, items accepted.
- Each derived fix in 1-2 sentences: what changed and why.
- Each judgement-call fix: what you changed, the alternative you didn't take, and how to revert it. This is the list the user scans to spot-check your decisions.
- Each open question, so the user sees what genuinely needs them.

Match the style of any existing audit section in the repo if one exists.

### Step 7: Report back

Concise summary to the user. Lead with the judgement calls, since those are what the user might want to revert:

```
Plan audit verdict: <READY | JUDGEMENT CALLS TO REVIEW | OPEN QUESTIONS>

Derived fixes applied (N):
- <what changed> | <agent> | <citation>

Judgement-call fixes applied — review these (N):
- <what I changed> → chose <X> over <Y> | <agent> | <citation>

Open questions (couldn't guess) (N):
- <finding + why it can't be resolved without you> | <agent> | <citation>

Considered but accepted (N):
- <finding>
```

If there are no open questions, the plan is READY — the user reviews the judgement calls (revert any they disagree with) and runs `/start-session`. If there are open questions, those are the only things that still need the user. Either way, stop; don't commit, don't run `/start-session` yourself.

## Distinguishing from /audit

| Aspect | /plan-audit | /audit |
|--------|-------------|--------|
| When | Pre-implementation | Post-implementation |
| Input | A phase plan doc | A diff (uncommitted or recent commits) |
| Focus | Plan completeness, feasibility, decomposition | Code correctness, spec alignment, test coverage |
| Apply fixes? | Yes — applies a best-guess fix for every finding it can, flags the judgement calls for review | Yes — mechanical code fixes applied; risky ones surfaced |
| Outcome | Plan is READY / JUDGEMENT CALLS TO REVIEW / OPEN QUESTIONS | Work is APPROVED / NEEDS FIXES |

## Rules

1. **Four parallel agents in ONE message.** Do not serialize them.
2. **Each agent gets a self-contained prompt.** It hasn't seen the conversation.
3. **Trust but verify agent citations.** Spot-check before applying a fix.
4. **Fix everything you can; flag the judgement calls.** Apply a best-guess resolution for every finding, including scope gaps and library/approach choices. Make the call, write it into the plan, and flag it in the report with the alternative so the user can revert. Only leave a finding unfixed when no defensible guess exists.
5. **Make every judgement call independently revertible.** The user must be able to undo one decision without unpicking the rest.
6. **Don't write code.** This skill revises the plan doc only.
7. **Don't auto-commit.** Apply fixes to the working tree and stop. The user reviews the judgement calls, then bundles and commits.
8. **Don't run if the plan looks routine.** A 1-day sub-phase doesn't need a plan audit. The skill is for substantial commitments.

## What NOT to Do

- Don't spawn agents serially. Single message, four calls.
- Don't punt a fixable finding to the user just because it involves a choice. Make the best guess, apply it, and flag it. Only genuinely-unguessable findings become open questions.
- Don't bury the judgement calls. The report must let the user see and revert each one at a glance.
- Don't apply a fix on a citation you haven't verified.
- Don't pad the report with non-findings. Fixes applied, judgement calls flagged, open questions, plus "considered but accepted" for surfaced-and-deemed-OK items.
