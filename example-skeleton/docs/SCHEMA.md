---
type: meta
status: active
summary: Frontmatter contract for ExampleApp. Every devlog, phase doc, knowledge file, lessons entry, state file, and spec uses these fields.
note_created: 2026-05-08
updated: 2026-05-08
---

# ExampleApp Frontmatter Schema

Single source of truth for what fields go in YAML frontmatter of every structured doc in this project. Skills like `/start-session`, `/end-session`, `/audit`, and `/find-session` query frontmatter via `grep`.

## Universal fields (every typed file)

| Field | Type | Purpose |
|-------|------|---------|
| `type` | enum | What kind of file this is. See per-type sections. |
| `summary` | string | One-line TLDR. |
| `note_created` | YYYY-MM-DD | Birth date. Immutable. |
| `updated` | YYYY-MM-DD | Last meaningful touch. |

## type: devlog

Devlogs at `docs/devlogs/YYYY-MM-DD-<topic>.md`. One per session.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `devlog` | |
| `status` | enum | `in-progress`, `complete` | Set on session start, flipped at `/end-session`. |
| `session_start` | HH:MM | 24-hour | Captured by `/start-session`. |
| `session_end` | HH:MM | 24-hour | Captured by `/end-session`. |
| `phase` | string | e.g., `1`, `2.5` | Phase number from implementation-plan. |
| `subphase` | string | e.g., `1a`, `2b.5` | Sub-phase identifier. Optional. |
| `approval` | enum | `pending`, `approved` | Set to `approved` only when phase fully signed off. |
| `summary` | string | one-liner | What happened this session. |

## type: phase

Phase docs at `docs/phases/phase-N-<slug>.md`.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `phase` | |
| `status` | enum | `planned`, `in-progress`, `approved`, `deferred` | Lifecycle. |
| `phase_number` | string | e.g., `1`, `2.5` | |
| `prerequisite` | string | | What needs to be done first. |
| `estimated_effort` | string | e.g., `5-7 days` | |
| `summary` | string | one-liner | Goal of the phase. |

## type: knowledge

Knowledge files at `docs/knowledge/<topic>.md`.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `knowledge` |
| `keywords` | list | Searchable tags. `/lookup` greps these. |
| `related` | list | Cross-references (file paths or playbook names). |
| `summary` | string | one-liner |
| `last_verified` | YYYY-MM-DD | Optional. When content was last cross-checked. |

## type: lessons

`docs/lessons.md`. Singular file. New entries at top.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `lessons` |
| `summary` | string | "Gotchas accumulator." |

Each entry inside follows: heading + Symptoms + Cause + Fix + Frequency + Discovered. No per-entry frontmatter.

## type: state

`docs/state.md`. Singular file. Slim snapshot of current focus.

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | `state` |
| `status` | enum | `active` |
| `summary` | string | One-line current focus. |
| `updated` | YYYY-MM-DD | Set every update. |

## type: spec

`docs/design/spec.md`. From `/spec-draft`.

| Field | Type | Allowed values | Purpose |
|-------|------|----------------|---------|
| `type` | string | `spec` | |
| `status` | enum | `draft`, `approved`, `superseded` | |
| `summary` | string | one-liner | |
| `note_created` | YYYY-MM-DD | | |
| `updated` | YYYY-MM-DD | | |

## YAML defensive quoting

- Any `summary:` value containing `: ` MUST be wrapped in double quotes.
- Wikilink-style fields stay quoted: `up: "[[Target]]"`.
- Values starting with `[`, `{`, `&`, `*`, `?`, `|`, `>`, `!`, `%`, `@`, or backtick should be quoted.

## Field discipline

- New devlogs default to `status: in-progress`. Flip to `complete` at `/end-session`.
- New phase docs default to `status: planned`. Flip to `in-progress` when work starts. Flip to `approved` when fully signed off.
- `updated:` reflects content changes only. Pure frontmatter tweaks don't count.
- Date format always `YYYY-MM-DD`. ISO 8601, no exceptions.

## Why this matters

Skills can answer questions via plain `grep`:

- "What's in progress right now?" → `grep -l "status: in-progress" docs/devlogs/`
- "What phases are planned?" → `grep -l "status: planned" docs/phases/`
- "Was last sub-phase approved?" → check most recent devlog `approval:` field
