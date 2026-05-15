---
type: meta
status: active
summary: Frontmatter contract for the project. Every devlog, phase doc, knowledge file, lessons entry, state file, and spec uses these fields.
note_created: __DATE__
updated: __DATE__
---

# Project Frontmatter Schema

This is the **single source of truth** for what fields go in the YAML frontmatter of every structured doc in this project. Both humans and agents reference this file. Skills like `/start-session`, `/end-session`, `/audit`, and `/find-session` query frontmatter via `grep`.

## Universal fields (every typed file)

| Field | Type | Purpose |
|-------|------|---------|
| `type` | enum | What kind of file this is. See per-type sections below. |
| `summary` | string | One-line TLDR. |
| `note_created` | YYYY-MM-DD | Birth date. Immutable. |
| `updated` | YYYY-MM-DD | Last meaningful touch. Update when content changes. |

## type: devlog

Devlogs live at `docs/devlogs/YYYY-MM-DD-<topic>.md`. One devlog per session.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `devlog` | |
| `status` | enum | `in-progress`, `complete` | Set on session start, flipped to `complete` at `/end-session`. |
| `session_start` | HH:MM | 24-hour | Captured by `/start-session`. |
| `session_end` | HH:MM | 24-hour | Captured by `/end-session`. |
| `phase` | string | e.g., `1`, `2`, `1.5` | Phase number from implementation-plan. |
| `subphase` | string | e.g., `1a`, `2b.5` | Sub-phase identifier. Optional. |
| `approval` | enum | `pending`, `approved` | Set to `approved` only when phase / sub-phase fully completed and signed off. |
| `summary` | string | one-liner | What happened this session. |

## type: phase

Phase docs live at `docs/phases/phase-N-<slug>.md`. One per phase.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `phase` | |
| `status` | enum | `planned`, `in-progress`, `approved`, `deferred` | Lifecycle. |
| `phase_number` | string | e.g., `1`, `2.5` | Number from implementation-plan. |
| `prerequisite` | string | e.g., `Phase 1 complete` | What needs to be done first. |
| `estimated_effort` | string | e.g., `5-7 days` | Rough time estimate. |
| `summary` | string | one-liner | Goal of the phase. |

## type: knowledge

Knowledge files live at `docs/knowledge/<topic>.md`. One per topic.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `knowledge` | |
| `keywords` | list | freeform list | Searchable tags. `/lookup` greps these. |
| `related` | list | freeform list of file paths or playbook names | Cross-references. |
| `summary` | string | one-liner | What this file covers. |
| `last_verified` | YYYY-MM-DD | optional | When the content was last cross-checked against current code or library docs. |

## type: lessons

The `docs/lessons.md` file. Singular, project-wide. New entries go at the top.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `lessons` |
| `summary` | string | One-line description (e.g., "Gotchas accumulator. New entries at top.") |

Each lesson entry inside the file follows: heading + symptoms + cause + fix + frequency + discovered-date. No per-entry frontmatter.

## type: state

The `docs/state.md` file. Singular, project-wide. Slim snapshot of what's hot right now. Updated by `/end-session` and `/checkpoint`.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `state` |
| `status` | enum | `active` |
| `summary` | string | One-line current focus. |
| `updated` | YYYY-MM-DD | Set every update. |

## type: spec

Design spec at `docs/design/spec.md`. Created by `/spec-draft`.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `spec` | |
| `status` | enum | `draft`, `approved`, `superseded` | Authoritative state of the spec. |
| `summary` | string | one-liner | What the spec covers. |
| `note_created` | YYYY-MM-DD | | First draft date. |
| `updated` | YYYY-MM-DD | | Last update. |

## type: playbook

Playbooks live in the active global playbook library, usually `~/.agents/playbooks/`, `~/.codex/playbooks/`, or `~/.claude/playbooks/` (or the configured `playbooks_path`). Cross-project, not in this project's docs.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `playbook` |
| `name` | string | Slug matching filename. |
| `keywords` | list | Searchable tags. |
| `applies_to` | list | Languages, libraries, platforms. |
| `last_verified` | YYYY-MM-DD | When claims were last checked against current docs. |
| `verified_against` | string | Specific version or commit. |
| `summary` | string | One-liner. |

## YAML defensive quoting

- Any `summary:` value containing `: ` (colon-space) MUST be wrapped in double quotes. Without quotes, YAML treats `: ` as a mapping-value separator and the parse fails (frontmatter shows as broken in tools).
- Wikilink-style fields (if used) stay quoted: `up: "[[Target]]"`.
- Any value starting with `[`, `{`, `&`, `*`, `?`, `|`, `>`, `!`, `%`, `@`, or `\`` should be quoted.

## Field discipline

- Default new devlogs to `status: in-progress`. Flip to `complete` at `/end-session`.
- Default new phase docs to `status: planned`. Flip to `in-progress` when work starts. Flip to `approved` when fully signed off.
- Default new knowledge files have no `last_verified` until you've cross-checked against current code. Add the date when you do.
- `updated:` reflects content changes only. Pure frontmatter tweaks don't count.
- Date format is always `YYYY-MM-DD`. ISO 8601, no exceptions.

## Why this matters

If every typed file follows this contract, agents can answer questions via plain `grep`:

- "What's in progress right now?" → `grep -l "status: in-progress" docs/devlogs/`
- "What phases are planned but not started?" → `grep -l "status: planned" docs/phases/`
- "What knowledge files were last verified before March?" → grep + date filter
- "Was the last sub-phase approved?" → check most recent devlog `approval:` field

Skills depend on this. Don't drift the schema without updating them.
