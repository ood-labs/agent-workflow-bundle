---
name: formalize-plan
description: Formalize a plan into phase docs and implementation plan
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
user-invocable: true
---

We just finished planning (via plan mode or discussion). Now formalize it into the project's documentation system and commit.

DO:
1. **Read the plan file** from the active agent plan directory (check `.agents/plans/`, `.codex/plans/`, then `.claude/plans/`; use the most recently written one) to understand what was planned
2. **Create a detailed phase document** at `docs/phases/phase-{N}-{slug}.md` with:
   - Overview and motivation
   - Problem statement (before/after if applicable)
   - Deliverables table (ID, feature, tool, actions, status)
   - Each sub-phase with: parameters, response schemas, UE APIs, implementation details, and an explicit **pass criterion** (definition-of-done provable in-transcript)
   - Files summary (new files, modified files, no-change files with reasons)
   - Implementation order
   - Verification plan (the proof method / testability contract — how each sub-phase is proven, e.g. tests, MCP readback, capture)
   - **Autonomy & human-in-the-loop** — see below; this is what lets the phase run under `/slash-goal` with minimal intervention
   - Example agent workflow
   - Dependencies

   **The Autonomy & human-in-the-loop section** is what makes a phase runnable as a single short goal. Design the plan for long autonomous stretches with human input batched into as few points as possible, then write the section to capture:
   - **Human-intervention points** — the specific moments a person is genuinely needed (a physical/taste check, an irreversible decision), batched so most of the phase runs without stopping. Order the sub-phases so these cluster rather than scatter.
   - **Gate tiers** — classify each pause as **self-serve** (automated check + log + `approval: pending` + continue; e.g. aesthetic sign-offs, the per-sub-phase approval cadence), **conditional-proceed** (a decision pre-authorized with a testable rule — "accept X if `<check>` passes, else stop"), or **hard-stop** (genuinely irreversible/unsettled: git history rewrite, spec edits, a core/upstream fork, an unsettled decision).
   - **Pre-authorizations** — the resolved conditional-proceed decisions, written so the loop can act on them without asking.
   - **Hard blockers** — the tier-3 list that should stop the run.

   A short `/slash-goal` then just points at this doc instead of re-encoding it.
3. **Update `docs/implementation-plan.md`**:
   - Add the new phase to the Phase Overview table with link to detailed plan
   - Add/update the phase section in the body (sub-phases table, MCP tools, dependencies, implementation order)
   - Update any "Future Phases" sections that referenced this phase as planned
4. **Update `AGENTS.md` and `CLAUDE.md`** Current Status sections when those files exist, so Codex and Claude Code see the same active phase
5. **Commit** all changes with message format: `docs(plan): Phase {N} - {Title}`
6. **Offer the goal.** After committing, if the phase doc has a complete Autonomy section, offer to run `/slash-goal` to emit a short completion-condition that points at this doc and drives the phase autonomously. (For substantial or multi-week phases, suggest `/plan-audit` first.) Don't auto-run either — just surface the next step.

DON'T:
- Mark anything as complete or approved (this is planning, not implementation)
- Write any C++ or TypeScript code
- Modify any plugin or MCP server source files
