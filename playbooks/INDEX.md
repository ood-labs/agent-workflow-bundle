---
type: playbook-index
summary: Master index of cross-project playbooks. Each row points to a self-contained architectural pattern.
---

# Playbooks INDEX

Cross-project architectural patterns. These travel with your install under the active agent home, usually `~/.agents/playbooks/`, `~/.codex/playbooks/`, or `~/.claude/playbooks/` (or whatever path is set as `playbooks_path`). Skills like `/lookup`, `/extract-playbook`, `/audit-playbooks`, and `/scaffold-project` read this index.

A playbook is **cross-project**: it teaches a pattern that recurs across projects. Project-specific reference belongs in the project's `docs/knowledge/`, not here.

## Active playbooks

| File | Keywords | Applies to | Last verified | Description |
|------|----------|------------|---------------|-------------|
| [mcp-co-development.md](mcp-co-development.md) | mcp, automation, ipc, zmq, state-tree, capture, rust, native-app | native-app, desktop, graphics, ai, cli-tool | 2026-05-08 | Build a native app and its Rust MCP server in lockstep. State tree as universal control surface, ZMQ REQ/REP IPC, multi-action MCP tools, capture system for visual verification. |

## Adding playbooks

Use `/extract-playbook` from inside any project. The skill scans `AGENTS.md`, `CLAUDE.md`, and `docs/knowledge/` for cross-project-shaped content, drafts a playbook, and adds a row here.

Manual additions: each playbook lives at `<playbooks_path>/<slug>.md` with frontmatter:

```yaml
---
type: playbook
name: <slug>
keywords: [comma, separated, tags]
applies_to: [language, library, platform]
last_verified: YYYY-MM-DD
verified_against: <version or commit hash>
summary: <one-liner>
---
```

After adding the file, append a row to this INDEX with: filename, keywords, applies_to, last_verified, one-line description.

## Vault path override

By default, playbooks live under the active agent home. To store them elsewhere (for example, inside an Obsidian vault for queryable cross-linking), set `playbooks_path` in the active agent settings file:

```json
{
  "playbooks_path": "/path/to/your/vault/01-lib/playbooks"
}
```

When this is set, `/extract-playbook` writes there, `/audit-playbooks` reads from there, and `/lookup` searches there in addition to the current project's `docs/knowledge/`.

## Auditing

`/audit-playbooks` walks every file here, flags entries past `last_verified` threshold (default 90 days), and (in Deep mode) spawns Explore agents to spot-check claims against current library docs.

## Archive

Outdated or superseded playbooks move to `<playbooks_path>/archive/` rather than getting deleted. Keeps the historical record, removes them from active discovery.
