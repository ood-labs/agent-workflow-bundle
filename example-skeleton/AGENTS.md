# Agent Instructions for ExampleApp

## Project Overview

ExampleApp is a native desktop image processing tool with a Dear ImGui frontend, GPU compute backend, and a Rust MCP server for end-to-end automation by coding agents. This is a sample project produced by `/scaffold-project`. Replace this paragraph with your own project description when using this skeleton as a starting point.

### Core Architecture
- **Image Pipeline**: GPU compute shaders (Vulkan or DirectX 11) for filters and transforms
- **State Tree**: Path-addressed parameter registry shared by UI, MCP, and project save/load
- **MCP Server**: Rust binary translating MCP calls to ZeroMQ JSON commands against the app
- **UI**: Dear ImGui in a single docked window with a parameter panel and preview

### Design Principles
1. **State tree is the source of truth** — every parameter lives there; UI and MCP read and write the same nodes
2. **Automation as first-class** — every feature ships with an MCP-testable surface before the UI is built
3. **GPU-first** — stay on the GPU; round-trip to CPU only for save and screenshot
4. **No hidden state** — anything that affects output goes in the state tree and persists with the project

---

## Project Structure

```
ExampleApp/
├── AGENTS.md
├── CLAUDE.md                     # Claude Code compatibility pointer or mirror
├── .agents/skills/               # Canonical project-specific skills
├── .codex/skills/                # Codex mirror when needed
├── .claude/skills/               # Claude Code mirror when needed
├── .gitignore
├── .mcp.json                     # Points at compiled mcp-server-rs binary
├── docs/
│   ├── SCHEMA.md                 # Frontmatter contract (copied from bundle templates)
│   ├── implementation-plan.md
│   ├── state.md                  # Current focus snapshot (updated by /end-session)
│   ├── lessons.md                # Gotchas accumulator (append-at-top)
│   ├── phases/
│   │   └── phase-1-mcp-foundation.md
│   ├── knowledge/
│   │   └── INDEX.md
│   ├── design/                   # Spec lands here if /spec-draft was run
│   ├── devlogs/                  # YYYY-MM-DD-{topic}.md, with frontmatter
│   ├── research_prompts/
│   ├── research_results/
│   └── agent-learnings/
├── src/
│   ├── main.cpp
│   ├── automation/
│   │   ├── state_tree.{cpp,h}
│   │   └── ipc_bridge.{cpp,h}
│   └── ui/
└── mcp-server-rs/
    ├── Cargo.toml
    └── src/
        ├── main.rs
        ├── ipc.rs
        └── tools/
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| GPU compute | Vulkan or DirectX 11 |
| UI | Dear ImGui |
| MCP server | Rust |
| IPC | ZeroMQ REQ/REP, JSON |
| Build | CMake (app), Cargo (MCP server) |

---

## Development Workflow

### Commit Message Format

```
<type>(<scope>): <description>
Types: feat, fix, docs, test, refactor, chore
```

---

## MCP Tools (planned)

| Tool | Domain | Actions |
|------|--------|---------|
| `app` | Lifecycle | ping, launch, kill, status |
| `state` | Parameters | tree, get, set, list_values, list_actions, invoke |
| `capture` | Output | screenshot, image |

---

## Available Skills

Global workflow skills installed via the Agent Workflow Bundle work in this project automatically: `/start-session`, `/checkpoint`, `/plan-audit`, `/audit`, `/end-session`, `/formalize-plan`, `/find-session`, `/research-prompt`, `/spec-draft`, `/scaffold-project`, `/slim-agent-md`, `/lookup`, `/extract-playbook`, `/audit-playbooks`.

No project-specific skills yet. Add the canonical copy under `.agents/skills/<skill-name>/SKILL.md` when a workflow becomes repetitive enough to warrant its own skill. Mirror to `.codex/skills/` or `.claude/skills/` when the active agent needs its own discovery path.

---

## Knowledge Base

Detailed reference in `docs/knowledge/`. Start with [INDEX.md](docs/knowledge/INDEX.md).

Search by keyword: `grep -rl "keyword" docs/knowledge/`

---

## Universal Rules (Apply to ALL Sessions)

1. **State tree first** — register parameters in the state tree before building UI or processing logic
2. **PING before features** — make sure end-to-end automation works before adding any non-trivial feature
3. **Test via MCP** — the agent verifies every feature end-to-end through the MCP surface; manual testing is the fallback
4. **Devlog every commit** — a commit without a devlog entry is incomplete

---

## Current Status

**Phase**: Phase 0 — Project Setup **Complete**. Phase 1 (MCP Foundation) planned, not started.

Detail in [docs/state.md](docs/state.md). Roadmap in [docs/implementation-plan.md](docs/implementation-plan.md).

Frontmatter contract: [docs/SCHEMA.md](docs/SCHEMA.md).

---

## What to Avoid

### Architecture
- **Bypass the state tree** — direct parameter mutation breaks UI sync, project save, and MCP control
- **Bolted-on automation** — adding MCP support after a feature ships costs more than building it in
- **CPU round-trips on the hot path** — stay on the GPU until you actually need pixels on disk

### Process
- **Skipping the devlog** — devlogs are how future sessions inherit context; an undocumented commit forces re-discovery
- **Marking work APPROVED before testing it through MCP** — if the automation surface can't drive the feature, the feature isn't done
