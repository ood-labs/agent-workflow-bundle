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
   - Each sub-phase with: parameters, response schemas, UE APIs, implementation details, and an explicit **pass criterion** (definition-of-done provable in-transcript). **The criterion must bite:** for any user-facing feature, at least one pass criterion must be a *visible/behavioral/executing* gate that is **false unless the experience actually exists** — "a human can SEE X on the canvas," "you can DO Y," "it RUNS and the output changes." Readback / log-line / "artifact exists" / "screenshot captured" criteria are necessary but never sufficient for a feature phase — a mock clears them. Screenshot criteria must assert what the image has to contain (a vision_eval-style content check), not just that a capture was taken.
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

   The **Delegation** section decides what the cheap tier may build (doctrine: `/delegate`). For each sub-slice write: **delegable** or **judge-only**; for a delegable slice, the **allowed files** it may touch, the **test command** that proves its pass criterion, and the **retry budget** (default 2). Default delegable: any slice whose pass criterion is a test or an executing check the worker can run itself. Judge-only: anything touching the spec, instruction files, git, an unsettled decision, or a criterion that needs a human eye. A delegable slice without allowed files and a test command is a plan defect.

   **Make the governing spec the acceptance bar, not a citation.** If the phase names a governing spec section, the pass criteria must be at least as strong as that section's requirements — the result will be checked against the phase doc, so the phase doc must not be a weaker bar than the spec. Trace each governing-spec requirement to a criterion that enforces it. Citing §X.Y in the Overview is not the same as verifying against it.

   **Every claim about the codebase is resolved, not remembered.** A plan is read later as fact, so anything in it that is merely plausible becomes a measurement nobody re-checks. Before writing a claim about the existing tree, resolve it this session:
   - **Name symbols at their resolved version.** Types, ops/node versions, ports, enum values, flags, functions, paths — read them out of the live source or registry. Never copy a version from a fixture or save file: a file written by an older build carries older versions and is not evidence of what is current.
   - **Cite connections by declared identifier, with the type on both ends** (`clone_grid_v12:source1`, `PortType::Geometry`), never in prose like "the object input." Prose is unverifiable, and an illegal connection described in prose will be built before anyone notices the system refuses it.
   - **Label every number MEASURED or ASSUMED.** A count, timing, size or population with a receipt, log or dump behind it is MEASURED and cites it. Anything arithmetic over other plan values, or with no source, is ASSUMED — and an ASSUMED value may never be used as a baseline, expected value or pass threshold. Most plan-vs-reality failures are an arithmetic number that got cited as a measurement a day later.
   - **Search the test registry before specifying any new test, gate or check.** Resolve the project's actual registry (`ctest --show-only=json-v1`, the runner's list command, the CI config) and read candidate sources, not just names. For each new instrument, either name the existing one it extends, imports or parameterises, or state with `file:line` why none can carry the claim. Naming a parent in prose is not reuse. If the tree already holds a family of near-identical copies, factor rather than add the next one.

   **Frame foundation/substrate phases honestly.** If a phase delivers only substrate (a data model, an MCP surface, an ID/serialization layer) and nothing a user can see, touch, or run yet, say so plainly in the title and Overview — "Phase 1 of N: durable model only; nothing visible or executable yet" — and name the companion phase that delivers the visible/executing feature. A word like "Model" or "Boundary" in the title must not let "substrate done" be reported later as "feature done."
3. **Update `docs/implementation-plan.md`**:
   - Add the new phase to the Phase Overview table with link to detailed plan
   - Add/update the phase section in the body (sub-phases table, MCP tools, dependencies, implementation order)
   - Update any "Future Phases" sections that referenced this phase as planned
4. **Update `AGENTS.md`** Current Status when it exists — CLAUDE.md is normally an `@AGENTS.md` import stub, so the one edit reaches both Codex and Claude Code. Never add sections to a stub; update CLAUDE.md too only in legacy projects where it still duplicates full content
5. **Commit** all changes with message format: `docs(plan): Phase {N} - {Title}`
6. **Offer the goal.** After committing, if the phase doc has a complete Autonomy section, offer to run `/slash-goal` to emit a short completion-condition that points at this doc and drives the phase autonomously. (For substantial or multi-week phases, suggest `/plan-audit` first.) Don't auto-run either — just surface the next step.

DON'T:
- Mark anything as complete or approved (this is planning, not implementation)
- Write any C++ or TypeScript code
- Modify any plugin or MCP server source files
