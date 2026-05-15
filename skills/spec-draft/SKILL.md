---
name: spec-draft
description: Generate a design specification document from research results and conversation context. Models on the Sentinel-2 spec template (Pick + Why Not blocks, Risk Register, Open Questions, Implementation Kickoff Checklist). Two modes: full (multi-week projects) and lite (2-3 week projects).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

# Spec Draft Skill

Produce `docs/design/spec.md` that captures every load-bearing architectural decision before code is written. The spec becomes the authority that `/audit` measures work against.

This skill is the bridge between research and scaffolding. Run it after deep research (research_prompts → research_results) and discussion of findings, before `/scaffold-project`.

## When to Use

- Multi-week project where architectural decisions are expensive to reverse
- After research_results have been digested in conversation
- Before `/scaffold-project` (the spec informs the implementation plan)
- User says "draft a spec", "write the spec", "design doc", "lock in the architecture"

## Modes

**Full mode** (default for multi-week projects, 15+ sections, modeled on Sentinel-2):
1. Header (status, authors, dates, purpose)
2. Vision and positioning
3. Core design principles (priority-ordered, numbered)
4. Commercial / licensing model (if applicable)
5. System architecture at a glance
6. Component / layer split
7. Per-layer technical specifics (rendering, scripting, plugin system, UI, etc., matched to the project)
8. Cross-platform considerations (if applicable)
9. Agent integration (if applicable)
10. Dependency and license matrix
11. MVP phasing
12. Risk register
13. Open questions and pending sign-offs
14. Implementation kickoff checklist

**Lite mode** (2-3 week projects, 8-10 sections):
1. Header
2. Problem statement
3. Architectural commitments (with Pick + Why Not blocks per decision)
4. Component boundaries
5. Data model
6. Performance targets
7. Non-goals
8. Risk register
9. Open questions
10. Success criteria + Implementation kickoff

## Workflow

### Step 1: Detect mode

Ask the user: "Is this a multi-week effort with non-trivial architecture risk (full mode), or a 2-3 week scoped project (lite mode)?" Default to lite if unclear. User can override.

### Step 2: Read context

Read every file in `docs/research_prompts/` and `docs/research_results/`. Read any existing `AGENTS.md`, `CLAUDE.md`, `docs/design/`, or `docs/strategy/` content. Read recent conversation transcripts if available (from the active agent transcript directory, such as `~/.codex/sessions/` or `~/.claude/projects/<project-key>/`).

If research results are sparse, surface this: "research_results has only N files. Want to draft anyway, or do more research first?"

### Step 3: Identify the load-bearing decisions

Walk the research findings and conversation. List every architectural decision that has been made (or needs to be made). For each:
- What is being decided
- What was picked (or "open")
- What alternatives were considered
- What rationale supports the pick
- What would have to be true for the pick to be wrong

This becomes the Architectural Commitments / Pick + Why Not blocks section.

### Step 4: Draft the spec

Write to `docs/design/spec.md`. Match the structure of the chosen mode. Each section follows these conventions:

- **Header block**: status (Draft / Approved / Superseded), authors, initial draft date, last updated, purpose statement
- **Pick + Why Not blocks** at every architectural decision: declare the pick in bold, then list rejected alternatives with one-line rationale each
- **Cross-references** with `§X.Y` notation when referencing other spec sections
- **Risk register** with severity (low / medium / high), mitigation, and owner
- **Open questions** as a first-class section with a tracking ID per question (Q1, Q2, ...)
- **Dependency and license matrix** as a table: dependency, version, license, verdict (clean / copyleft-quarantined / blocked)
- **MVP phasing** as a table: milestone, capabilities, deferred-to-later, ship target
- **Frontmatter** at the top of the file: `type: spec`, `status: draft | approved`, `summary`, `note_created`, `updated`

### Step 5: Surface gaps explicitly

After the draft, list any sections that are stub-level or incomplete. Don't pretend the draft is finished. Surface:
- Decisions still open (Q1, Q2, ...)
- Sections with placeholder content
- Performance targets without methodology
- Dependencies without license verdicts

### Step 6: Iterate with the user

Present the draft. Ask: "What's missing, what's wrong, what's over-committed?" Iterate until the user accepts the draft as ready for `/scaffold-project`.

### Step 7: Mark status

When the user accepts, change frontmatter `status:` from `draft` to `approved`. Set `updated:` to today. Optionally commit with `docs(spec): initial spec draft for <project name>`.

## Reference: Sentinel-2 spec

The Sentinel-2 design spec is the strongest exemplar of this format. It uses 27 sections, explicit Pick + Why Not Alternatives at every decision, spike references for measured evidence, cross-reference notation (§X.Y), risk register with severity, open questions tracked by ID, dependency + license matrix, MVP phasing table, and an implementation kickoff checklist.

If the user has a similar prior spec accessible, read it first and match its tone, depth, and section structure.

## Rules

1. **Decisions, not options.** The spec captures decisions made. Open questions live in the Open Questions section, not embedded in commitments.
2. **Pick + Why Not.** Every architectural decision shows what was picked and what was rejected, with rationale. Makes the spec navigable for future readers.
3. **Cite evidence.** When a pick rests on a benchmark or vendor claim, cite the source. Performance numbers without methodology are placeholders, not commitments.
4. **Risk register has owners.** Every risk has a name attached (the user, in solo projects).
5. **Implementation kickoff is concrete.** "Set up Wasmtime + WIT bindings" beats "begin runtime work".
6. **Open questions get IDs.** Q1, Q2, ... so they can be referenced and tracked.
7. **Status header is accurate.** Don't mark Approved unless the user has approved it.

## What NOT to Do

- Don't research the topic. The research is upstream. The spec compresses findings into decisions.
- Don't pad with platitudes. Every section earns its place.
- Don't lock in things that should stay open. If the user wants to defer, that's a Q-numbered open question, not a commitment.
- Don't skip Risk Register or Open Questions because they feel pessimistic. Their absence makes the spec brittle.
- Don't auto-commit. Let the user own the commit.
