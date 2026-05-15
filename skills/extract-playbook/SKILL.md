---
name: extract-playbook
description: Distill cross-project knowledge from the current project's agent instructions or knowledge base into a playbook for the global library. Use when you realize a pattern you just solved will recur across projects.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

# Extract Playbook Skill

Take pattern-shaped content from the current project and refactor it into a self-contained architectural playbook in the global library.

A playbook is cross-project. It teaches a pattern that will recur across multiple projects. Project-specific reference stays in the project's `docs/knowledge/`.

## When to Use

- You're working in project B and recognize a pattern you already solved in project A
- A "Known Pitfalls" section has accumulated 5+ entries that aren't project-specific
- After solving a meaty architectural problem, you realize the solution shape will recur
- User says "extract a playbook", "this should be a playbook", "save this as cross-project"

## Modes

**Mode 1: Topic-named** (`/extract-playbook <topic>`)

User names the topic. Skill scans the current project for content matching the topic and proposes a playbook draft.

**Mode 2: Scan** (`/extract-playbook` with no args)

Skill scans the current project's `AGENTS.md`, `CLAUDE.md`, and `docs/knowledge/` for cross-project-shaped content and proposes candidates. User picks which to extract.

## Workflow

### Step 1: Resolve playbooks path

Read `playbooks_path` from the active agent settings file. Check `.agents`, `.codex`, then `.claude`. If unset, use the first existing playbook directory in this order: `~/.agents/playbooks/`, `~/.codex/playbooks/`, `~/.claude/playbooks/` (or `%USERPROFILE%\<agent-home>\playbooks\` on Windows).

Verify the path exists. If missing, create the directory with an `INDEX.md` initialized using this format:

```markdown
---
type: playbook-index
summary: Master index of cross-project playbooks.
---

# Playbooks INDEX

Cross-project architectural patterns. Travel via the workflow bundle install.

## Active playbooks

| File | Keywords | Applies to | Last verified | Description |
|------|----------|------------|---------------|-------------|
```


### Step 2: Identify candidates (Mode 2 only)

Walk `AGENTS.md`, `CLAUDE.md`, and `docs/knowledge/`. Score each section by cross-project applicability:
- High: pattern names a non-project-specific concern (a library, an OS, a protocol, a deployment target)
- Medium: pattern is library-specific, library widely used (e.g., ImGui, ZeroMQ, TensorRT)
- Low: pattern is project-specific (custom architecture, project features)

Surface top candidates with brief description and source location. User picks 1-N to extract.

### Step 3: Check for existing playbook

For each topic to extract, search `<playbooks_path>/INDEX.md` and the playbook files for an existing match. If found, ask the user: extract as new, merge into existing, or update existing?

### Step 4: Draft the playbook

Each playbook follows this structure:

```markdown
---
type: playbook
name: <topic-slug>
keywords: [comma, separated, tags]
applies_to: [language, library, platform]
last_verified: YYYY-MM-DD
verified_against: <version or commit hash where applicable>
summary: <one-liner>
---

# <Topic Title>

## What this is
1-2 paragraph summary. What problem does it solve, when does it apply.

## Architecture
Diagrams, layer breakdowns, key abstractions.

## Implementation
Code examples, API patterns, gotchas in narrative form.

## Pitfalls
Specific gotchas with symptom + cause + fix.

## When to use this pattern
Bullet list of situations where this is the right pattern.

## When NOT to use this pattern
Bullet list of situations where this pattern is overkill or wrong.

## Source
Original encounter: <project name + brief context>
Distilled: YYYY-MM-DD
```

Lift content from the source instruction files and knowledge files, but rewrite for project-agnostic phrasing. Replace project-specific names with generic terms.

### Step 5: Show draft for review

Show the playbook draft to the user. Surface:
- Topic name and slug (becomes filename)
- Keywords (used by INDEX search and `/lookup`)
- Source sections in the original project being extracted
- Any phrasing that's still project-specific and may need rewording

User approves, edits, or rejects.

### Step 6: Apply

On approval:
1. Write `<playbooks_path>/<slug>.md`
2. Append a row to `<playbooks_path>/INDEX.md` with: filename, keywords, applies_to, one-line description, last_verified
3. In the source project, optionally replace the extracted content with a one-line pointer (`See playbook: <playbooks-path>/<slug>.md`). User chooses whether to replace, leave a pointer alongside, or leave intact.
4. If updating an existing playbook, bump `last_verified` to today's date

### Step 7: Report

Summary:
- Playbook(s) written and where
- INDEX.md updated
- Source content trimmed (or left intact, per user choice)

## Distinguishing playbooks from knowledge files

| Aspect | Playbook (global library) | Knowledge file (docs/knowledge/) |
|--------|----------------------------------|----------------------------------|
| Scope | Cross-project | Project-specific |
| Audience | Future projects you haven't started yet | Current project's agents and humans |
| Lifetime | Years (until pattern dates) | Project lifetime |
| Updates | Via `/extract-playbook update` mode | Edit-in-place during sessions |

## Rules

1. **Cross-project test**: would this pattern apply if you started a new project tomorrow with a similar tech stack? Yes → playbook. No → stays in `docs/knowledge/`.
2. **Project-agnostic phrasing.** Strip project-specific names, replace with role-based terms.
3. **last_verified is honest.** Set to today only if you've actually checked the pattern is still accurate.
4. **No silent overwrites.** If a playbook of the same name exists, ask before overwriting or merging.
5. **One topic per playbook.** Don't bundle "everything CUDA" if there are 4 distinct patterns. Split.
6. **INDEX is the source of truth for discovery.** Every playbook gets an INDEX entry.

## What NOT to Do

- Don't extract project-specific reference. That stays in `docs/knowledge/`.
- Don't auto-commit. The user owns the commit (and decides whether the project repo or the global playbook gets it).
- Don't extract content you haven't verified. If the pattern was a one-time hack, it's not a playbook.
- Don't skip the keyword tags. `/lookup` and `/audit-playbooks` both rely on them.
