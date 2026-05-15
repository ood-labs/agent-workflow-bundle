---
name: slim-claude-md
description: Refactor bloated AGENTS.md or CLAUDE.md files into lean primary instructions plus topic-grouped knowledge files (and where appropriate, new skills). Use when an agent instruction file exceeds 25,000 characters, drifts toward the 40,000 hard ceiling, or has accumulated detailed reference material that belongs in docs/knowledge/.
user-invocable: true
---

# Slim Agent Instructions Skill

Refactor an `AGENTS.md` or `CLAUDE.md` that has grown too large into:
- Lean primary instruction files (hard ceiling: 40,000 characters each; aim for 20,000 to 25,000)
- Topic-grouped knowledge files in `docs/knowledge/` with keyword tags
- New skills in `.agents/skills/` when content is workflow-shaped, mirrored to `.codex/skills/` or `.claude/skills/` when needed

The refactor preserves information. Nothing is deleted unless it is genuinely stale or duplicated by current code. Detailed reference material moves to knowledge files; the instruction files keep short pointers.

## When to Use

- AGENTS.md or CLAUDE.md exceeds 40,000 characters (hard ceiling, must act)
- AGENTS.md or CLAUDE.md exceeds 25,000 characters and session startup feels slow
- A new agent in the project struggles to find specific reference because CLAUDE.md is too long to read carefully
- "Known Pitfalls" sections have grown into multi-page collections
- The Current Status section reads like a series of devlog summaries instead of a one-paragraph snapshot
- User says "slim AGENTS.md", "slim CLAUDE.md", "compress instructions", "refactor CLAUDE.md", "extract knowledge"

## What Stays in Instruction Files

These sections remain in AGENTS.md and/or CLAUDE.md regardless of size:

| Section | Why it stays |
|---------|--------------|
| Project overview (1 paragraph) | Sets context for every session |
| Core architecture (bullets) | High-level mental model |
| Design principles | Decision frame for the agent |
| Project structure (tree) | Navigation aid |
| Tech stack table | Quick reference |
| Available skills table | Discovery surface |
| Universal rules | Cross-cutting constraints |
| Current status (1 to 3 lines) | Where we are now |
| Knowledge Base pointer | Index entry to docs/knowledge/ |
| What to Avoid (high-level only) | Anti-patterns |

## What Moves to Knowledge Files

Content shapes that belong in `docs/knowledge/`:

- **Library-specific reference**: one file per library (e.g., `imgui.md`, `tensorrt.md`, `nvenc.md`).
- **Subsystem deep dives**: full reference for one subsystem (e.g., `state-tree.md`, `pipeline-lifecycle.md`).
- **Debugging recipes**: step-by-step procedures for diagnosing recurring issues.
- **Domain conventions**: naming, file layout, parameter conventions specific to the project.
- **Detailed feature reference**: content that reads like a manual rather than a reminder.

## What Moves to docs/lessons.md

The lessons file is the gotchas accumulator. Content moves here when:

- It's a "Known Pitfalls" entry with symptom + cause + fix shape
- The pattern is one-time or recurring (not architectural reference)
- It would benefit from chronological accumulation (lessons.md is append-at-top by date)

Examples of lessons-shaped content: "macOS xattr quarantine breaks code signing", "ImGui 1.92 needs renderer-owned font textures", "ZMQ REQ socket needs reset after timeout".

Format each entry: `## YYYY-MM-DD — Short title` heading, then **Symptoms** / **Cause** / **Fix** / **Frequency** / **Discovered** fields.

Knowledge files are structured (one topic per file). lessons.md is the running gotcha log. Library-specific gotcha **collections** (5+ entries on the same library) usually still go to a knowledge file; one-off pitfalls go to lessons.md.

## What Moves to Cross-Project Playbooks

If a section in AGENTS.md or CLAUDE.md describes an architectural pattern that would recur across projects (not project-specific reference), suggest `/extract-playbook` instead of moving to local knowledge. Don't move it as part of `/slim-claude-md`; surface it as a candidate. The user runs `/extract-playbook` separately to write to the active global playbook library.

Examples: "MCP co-development pattern", "Windows distribution recipe", "TensorRT engine packaging pipeline".

## What Moves to Skills

A piece of content is skill-shaped (not knowledge-shaped) when:

- It has clear "When to Use" triggers
- It has step-by-step workflow with discrete checkpoints
- It describes an action to perform rather than reference to look up
- The procedure spans multiple tools (Read, Edit, Bash, Agent)

Examples: building TensorRT engines, packaging a dist build, uploading to a CDN, scaffolding a new pipeline component, running a release.

## What Moves to Phase Docs / Devlogs

Sometimes "Current Status" accumulates content that really belongs elsewhere:

- Multi-paragraph descriptions of completed phases → already covered by `docs/devlogs/<date>-<topic>.md`
- "Open bug" notes that have a phase or sub-phase tracking them → reference the phase doc
- "Next" planning lists that overlap `docs/implementation-plan.md` → trim and link

If you find Current Status quoting devlogs verbatim, the canonical home is the devlog. Keep one or two sentences in the instruction file and link out.

## Workflow

### Step 1: Inventory

1. Read `AGENTS.md` and `CLAUDE.md` when present. Record total character count for each.
2. Read `docs/knowledge/INDEX.md` if it exists. List existing knowledge files with their keyword tags.
3. List existing skills under `.agents/skills/`, `.codex/skills/`, `.claude/skills/`, and the matching global skill homes.
4. Read `docs/implementation-plan.md` Phase Overview table to know what phases exist.
5. Glob `docs/devlogs/` to know what devlogs exist.

If both instruction files are under 25,000 characters, report the counts and stop. The files do not need slimming.

### Step 2: Section-by-section analysis

Walk every `##` heading in AGENTS.md and CLAUDE.md. For each section, pick one verdict:

| Verdict | Action |
|---------|--------|
| Keep | Stays verbatim |
| Compress | Trim to 1 to 3 sentences, leave the heading |
| Extract to knowledge | Move full content to a knowledge file, replace with a 1-line pointer |
| Extract to new skill | Move to a new `SKILL.md`, replace with a row in the Available Skills table |
| Merge with existing | Append to an existing knowledge file or skill |
| Delete | Stale, duplicated, or contradicted by current code |

Be specific. Cite line ranges from the source instruction file. Do not classify as Delete unless you have verified the content is no longer accurate (read the relevant code or recent devlogs).

### Step 3: Plan

Present a written plan to the user before applying any changes:

```
Current size: <N> characters
Target size: < 40,000 (hard), aim for 20,000-25,000

Sections kept verbatim:
  - <heading> (~<N> chars)
  - ...

Sections compressed:
  - <heading>: <N> -> <M> chars (saved <N-M>)
  - ...

New knowledge files:
  - docs/knowledge/<topic>.md  [keywords: a, b, c]  (from instruction file lines X-Y)
  - ...

New skills:
  - .agents/skills/<name>/SKILL.md  (from instruction file lines X-Y)
  - ...

Sections merged:
  - instruction file "<heading>" -> appended to docs/knowledge/<existing>.md
  - ...

Sections deleted (with reason):
  - <heading>: <reason — verified against current code or recent devlog>
  - ...

Estimated instruction file sizes after refactor: AGENTS.md ~<N> chars, CLAUDE.md ~<N> chars
```

Wait for approval before proceeding. Surface anything ambiguous as an open question. Do not guess.

### Step 4: Pre-flight checks

1. Verify git working tree is clean. If dirty, suggest committing first. This refactor touches many files; a clean baseline makes it easy to revert.
2. Verify `docs/knowledge/` exists; create with an `INDEX.md` stub if missing.
3. Verify `.agents/skills/` exists if any new skills are planned; mirror to `.codex/skills/` or `.claude/skills/` only when needed.

### Step 5: Apply

1. Write each new knowledge file. Line 1: `# <Topic> Reference`. Line 2: `<!-- keywords: comma, separated, tags -->`. Body: the extracted content, lightly edited for standalone readability (resolve any "see above" or "as discussed" references that no longer have local context).
2. Append a row to `docs/knowledge/INDEX.md` for each new file.
3. Write each new skill (`.agents/skills/<name>/SKILL.md`) with proper frontmatter (`name`, `description`, `user-invocable: true`).
4. Rewrite AGENTS.md and/or CLAUDE.md with the surviving sections plus short pointers where content was extracted. Preserve the original section order; agents have muscle memory for where things live.
5. Update the Available Skills table in the instruction files if new skills were created.
6. Update the Knowledge Base section in the instruction files to reflect the new files (or just point at `docs/knowledge/INDEX.md`).

### Step 6: Verify

1. Count characters in the new instruction files. If any are over 40,000, repeat Step 2 with a stricter eye for what really has to stay.
2. Verify each new knowledge file has the `<!-- keywords: ... -->` header on line 2.
3. Verify `docs/knowledge/INDEX.md` has rows for every file in `docs/knowledge/` (catch any drift).
4. Spot-check 2 to 3 knowledge file pointers in the instruction files and confirm they resolve to the right file.
5. If any sections were merged into existing knowledge files, re-read those files to confirm the appended content fits the file's topic and tone.

### Step 7: Report

Final report to the user:

- Before / after character counts (AGENTS.md and/or CLAUDE.md)
- New knowledge files with paths and keyword tags
- New skills with paths
- Sections deleted with reasons
- Suggested commit message: `docs: slim agent instructions, extract <N> knowledge files`

Do not commit automatically. Show the suggested message and let the user run `/end-session` or commit manually.

## Rules

1. **Preserve information.** Nothing is deleted unless it is stale or duplicated. When in doubt, extract.
2. **40,000 characters is a hard ceiling.** 20,000 to 25,000 is the target.
3. **Keep section order.** Don't reorganize instruction files while slimming. Same headings, smaller bodies.
4. **One topic per knowledge file.** Don't bundle "everything CUDA" if there are four distinct concerns. Split granularly.
5. **Keywords on line 2 of every knowledge file.** The `/lookup` skill depends on this.
6. **No conversation leaks in extracted content.** Rewrite "(see above)" and "(as discussed earlier)" references to be self-contained.
7. **Always show the plan before applying.** This is a heavy refactor. Preview, then apply.
8. **Don't invent skills.** Extract to a new skill only when content is genuinely procedure-shaped. Reference material goes to knowledge files.
9. **Preserve the project's writing conventions.** If the project's instruction files forbid em dashes or contrastive phrasing, the extracted knowledge files follow the same rules.
10. **Warn on dirty git state.** Recommend committing first.

## What NOT to Do

- Don't compress Universal Rules. They're short and they belong in the instruction files.
- Don't merge unrelated topics into one knowledge file to reduce file count. Future search expects topic-granular files.
- Don't delete the Project Overview, Architecture, or Current Status.
- Don't run on dirty git state without warning.
- Don't change the project's writing conventions while extracting.
- Don't skip the plan in Step 3. Going straight from analysis to application is how good information gets accidentally deleted.
- Don't auto-commit. Let the user own the commit.
