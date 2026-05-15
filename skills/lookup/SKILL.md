---
name: lookup
description: Search the current project's knowledge base AND the global cross-project playbooks library by keyword. Returns ranked matches with citations. Use when an agent or user wants to recall a project-specific pattern, a cross-project architectural pattern, or a gotcha without reading the whole library.
allowed-tools: Read, Glob, Grep, Bash
user-invocable: true
---

# Lookup Skill

Search two places:
1. `docs/knowledge/` in the current project — project-specific reference
2. The active global playbook library — cross-project architectural patterns

Each knowledge file uses YAML frontmatter `keywords: [a, b, c]` (or legacy `<!-- keywords: ... -->` on line 2). Each playbook uses YAML frontmatter `keywords: [a, b, c]` and `applies_to: [language, library, platform]`.

## When to Use

- Agent encounters a topic and wants to check whether the project has prior reference
- User says "look up X" or "what does the knowledge base say about Y"
- Before implementing something that might already be documented

## Workflow

### Step 1: Identify keywords

Extract 1 to 3 keywords from the user's request. Strip filler words.

### Step 2: Resolve search paths

The two search roots:
1. `docs/knowledge/` in the current project
2. The playbooks library — read `playbooks_path` from the active agent settings file. Check `.agents`, `.codex`, then `.claude`. If unset, use the first existing playbook directory in this order: `~/.agents/playbooks/`, `~/.codex/playbooks/`, `~/.claude/playbooks/` (or `%USERPROFILE%\<agent-home>\playbooks\` on Windows).

If neither exists, surface that explicitly: "no knowledge base or playbook library found in scope."

### Step 3: Search

Run `grep -rl "<keyword>" <each-path>` for both roots. Files match if any of:
- Frontmatter `keywords:` list contains the keyword
- Legacy `<!-- keywords: ... -->` line on line 2 contains the keyword
- File body contains the keyword

Also scan each library's `INDEX.md` File Directory table.

For playbook results, also consider `applies_to:` matches (e.g., search for "rust" matches playbooks where `applies_to: [rust, ...]`).

### Step 4: Read and summarize

Read the matching files. Return:
- The file path
- The most relevant section (heading + 2 to 3 bullets or a code block)
- A pointer to the full file if more context is needed

### Step 5: Report

Present results grouped by source:

```
Project knowledge (docs/knowledge/):
- <file> — <snippet>

Cross-project playbooks:
- <file> — <snippet>
```

If multiple files match, rank by relevance (frontmatter keyword exact match > body match). If nothing matches in either source, say so explicitly so the user knows the topic isn't covered yet (and may want to add it after solving the problem, via direct knowledge file write or `/extract-playbook`).

## Rules

1. **Don't fabricate.** If the knowledge base doesn't have an answer, say so. Don't invent entries.
2. **Cite the file.** Every claim should reference the source file by path.
3. **Match exact terms.** If the user asks about "ZMQ" don't substitute "ZeroMQ" silently. Note both spellings if both appear.
4. **Project-agnostic.** This skill operates on whatever project the agent is currently running in. It does not assume any particular project's content.
