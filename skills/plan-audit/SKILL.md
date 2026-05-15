---
name: plan-audit
description: Pre-implementation three-agent audit on a phase plan (spec-alignment, toolchain-feasibility, sub-phase decomposition). Run after /formalize-plan, before starting work. Catches plan-level issues before code is written.
allowed-tools: Agent, Read, Glob, Grep, Bash, WebFetch, WebSearch
user-invocable: true
---

# Plan Audit Skill

Run a three-agent audit on a phase plan BEFORE implementation begins. Catches gaps, infeasible toolchain assumptions, and bad sub-phase decomposition while they're cheap to fix.

This is the pre-implementation counterpart to `/audit` (which runs after work is done). Same agent infrastructure, different inputs and prompts.

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

### Step 3: Spawn three Explore agents in parallel

Send a single message with three Agent tool calls (`subagent_type=Explore`). Each agent gets a self-contained prompt: which plan to audit, what to check, the doctrine summary, and what shape the report should take.

**Spec-alignment agent**: does the plan deliver what the spec, research, and prior conversation say is needed? Trace each major deliverable in the plan back to a spec section, research finding, or design decision. Flag features in the plan with no traceability. Flag spec areas the plan should cover but doesn't. Cite §X.Y when referencing spec sections.

**Toolchain-feasibility agent**: do the libraries, APIs, SDKs, and tools the plan assumes exist and behave as the plan assumes? Check version compatibility against current platform support matrices. Check recent API changes (breaking changes in the last 6-12 months). Check whether real-world performance numbers in the plan are achievable (search for benchmarks, GitHub issues, vendor docs). Use WebFetch/WebSearch when the plan rests on a vendor claim. Flag any "this should work" that isn't backed by evidence.

**Sub-phase decomposition agent**: is the work decomposed so each sub-phase can be verified independently? Are dependencies between sub-phases explicit? Hidden ordering constraints? Is each sub-phase shippable in 1-2 sittings (1-3 days work)? Flag mega-phases (>1 week of work) that should be split. Flag dependencies that aren't named. Flag sub-phases without pass criteria.

Each agent reports under 800 words, ranked findings, file:line citations where relevant.

### Step 4: Synthesize and rank

Collect the three reports. Rank findings:

- **Blocker**: plan is fundamentally wrong on this point. Don't start work until resolved. (e.g., "the chosen library was deprecated 6 months ago", "phase has no traceability to spec")
- **Fix-before-implementing**: meaningful gap or risk. Resolve before starting. (e.g., "sub-phase 3 has no pass criteria", "library version assumed in plan doesn't exist")
- **Nice-to-resolve**: weak point that would benefit from clarification but isn't urgent.
- **Considered but accepted**: surface so the user knows it was thought about, but no action needed.

### Step 5: Report

Concise summary to the user:

```
Plan audit verdict: <READY | FIXES NEEDED | BLOCKED>

Blockers (N):
- <finding> | <agent> | <citation>

Fix-before-implementing (N):
- <finding> | <agent> | <citation>

Nice-to-resolve (N):
- <finding>

Considered but accepted (N):
- <finding>
```

If verdict is READY, the user can run `/start-session` and begin. If FIXES NEEDED or BLOCKED, surface the open decisions. The user revises the plan or accepts the gaps explicitly.

### Step 6: Document (optional)

If the user wants to memorialize the audit, append a "Plan audit findings" section to the phase doc with the verdict, resolved items, and accepted gaps. Otherwise the audit is ephemeral.

## Distinguishing from /audit

| Aspect | /plan-audit | /audit |
|--------|-------------|--------|
| When | Pre-implementation | Post-implementation |
| Input | A phase plan doc | A diff (uncommitted or recent commits) |
| Focus | Plan completeness, feasibility, decomposition | Code correctness, spec alignment, test coverage |
| Apply fixes? | No, surfaces only | Yes, mechanical fixes applied |
| Outcome | Plan is READY / NEEDS FIXES / BLOCKED | Work is APPROVED / NEEDS FIXES |

## Rules

1. **Three parallel agents in ONE message.** Do not serialize them.
2. **Each agent gets a self-contained prompt.** It hasn't seen the conversation.
3. **Trust but verify agent citations.** Spot-check before reporting blockers.
4. **Don't write code or revise the plan.** This skill surfaces findings; the user decides how to address them.
5. **Don't auto-commit.** Wait for the user.
6. **Don't run if the plan looks routine.** A 1-day sub-phase doesn't need a plan audit. The skill is for substantial commitments.

## What NOT to Do

- Don't spawn agents serially. Single message, three calls.
- Don't apply fixes. The user resolves the findings, not this skill.
- Don't pad the report with non-findings. Findings only, plus "considered but accepted" for surfaced-and-deemed-OK items.
