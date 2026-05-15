---
name: audit-playbooks
description: Walk the global playbook library, flag stale entries, optionally spawn Explore agents to verify each playbook's claims against current library docs. Run quarterly or before a major project that depends on a playbook.
allowed-tools: Agent, Read, Edit, Glob, Grep, Bash, WebFetch, WebSearch
user-invocable: true
---

# Audit Playbooks Skill

Sweep the global playbook library and surface:
- Playbooks past their `last_verified` threshold (default 90 days)
- Playbooks whose claims may no longer match current library / SDK / platform docs
- Playbooks with broken cross-references or missing INDEX entries

This skill complements `/extract-playbook`: extract creates and updates, audit checks and flags.

## When to Use

- Quarterly review of the playbook library
- Before starting a major project that will rely on one or more playbooks
- After a major version bump in a library that one or more playbooks reference (e.g., ImGui 1.92 → 2.0)
- User says "audit the playbooks", "check the playbooks", "are the playbooks still good?"

## Modes

**Mode 1: Quick** — only checks `last_verified` dates and INDEX consistency. No external research. Fast (under a minute).

**Mode 2: Deep** — quick checks plus spawns Explore agents to spot-check each playbook's claims against current docs. Slower (5-10 minutes per playbook), more accurate.

User picks. Default to Quick.

## Workflow

### Step 1: Resolve playbooks path

Read `playbooks_path` from the active agent settings file. Check `.agents`, `.codex`, then `.claude`. If unset, use the first existing playbook directory in this order: `~/.agents/playbooks/`, `~/.codex/playbooks/`, `~/.claude/playbooks/`.

### Step 2: Inventory

Glob `<playbooks_path>/*.md`. Read each playbook's frontmatter. Build a working list:
- name
- last_verified
- applies_to
- keywords
- file path

Read `<playbooks_path>/INDEX.md`. Cross-check: every playbook has an INDEX row, every INDEX row points to an existing file.

### Step 3: Quick audit

For each playbook:
1. Check `last_verified` against today. If older than threshold (default 90 days, override via argument), flag as stale.
2. Check INDEX entry exists and matches frontmatter (keywords, applies_to).
3. Check file is valid markdown with parseable frontmatter.

### Step 4 (Deep mode only): Library / SDK verification

Spawn one Explore agent per playbook. Each agent gets:
- The playbook content
- The `applies_to` list
- Instruction: verify each major claim in the playbook against current library / SDK / platform docs. Use WebFetch and WebSearch. Flag claims that may be outdated. Cite the doc URL where each claim was verified or contradicted.

Each agent reports under 500 words: claims verified, claims contradicted, unable-to-verify.

### Step 5: Report

```
Playbook audit verdict:

Audited: N playbooks
Stale (last_verified > 90 days): N
- <playbook name> (last_verified: YYYY-MM-DD)
- ...

Outdated claims (Deep mode only): N
- <playbook>: <claim> contradicted by <doc URL>
- ...

INDEX issues: N
- INDEX missing entry for <file>
- INDEX entry points to nonexistent file <file>

Suggested actions:
- Run /extract-playbook update <name> for the N stale playbooks
- Manually review and fix the N INDEX issues
- Decide on the N contradicted claims (update the playbook, or remove)
```

### Step 6: Apply (optional)

For mechanical fixes, apply on user approval:
- Add missing INDEX entries
- Remove dangling INDEX rows pointing at nonexistent files

For content updates (stale playbooks, contradicted claims), surface to the user. Don't auto-edit playbook bodies.

## Rules

1. **Quick mode is fast and offline.** Suitable for routine sweeps.
2. **Deep mode uses external research.** Reserve for major reviews.
3. **Don't auto-edit playbook content.** Surface findings, let the user decide.
4. **INDEX consistency fixes are safe.** Apply automatically with user approval.
5. **Threshold is configurable.** Default 90 days, override via argument: `/audit-playbooks 30` for a tighter sweep.

## What NOT to Do

- Don't run Deep mode without warning the user about runtime (5-10 minutes per playbook).
- Don't bump `last_verified` dates without actually verifying. The date earns its keep only by being honest.
- Don't delete playbooks. If outdated, suggest archiving (move to `<playbooks_path>/archive/`).
