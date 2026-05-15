---
name: scaffold-project
description: Create the full development system skeleton for a new project — AGENTS.md, Claude Code compatibility, implementation plan, knowledge base, skills, phases, devlogs, research docs, and git repo. For non-web apps, also scaffolds an MCP co-development surface (Rust MCP server + state tree + ZMQ IPC).
user-invocable: true
---

# Scaffold Project Skill

Bootstrap a new project with the full Aperture-style development system. Creates the documentation infrastructure, knowledge base, skill templates, implementation plan, and code skeleton — everything an agent needs to work effectively across sessions.

## When to Use

- Starting a brand new project from scratch
- Setting up the agent development system in an existing project that doesn't have one
- User says "create a new project", "scaffold", "set up the dev system", etc.

## Before You Start

Gather from the user (ask if not clear):

1. **Project name** — used for folder name and repo (e.g., `aperture-blender`)
2. **One-sentence description** — what does it do?
3. **Parent directory** — where to create it (default: `C:\Users\cerspense\Documents\dev\`)
4. **Tech stack** — language(s), frameworks, key dependencies
5. **Architecture overview** — major components (e.g., "MCP server + Blender addon")
6. **Design principles** — 3-6 guiding principles for the project
7. **Initial skills needed** — what workflows will the agent need? (e.g., "mesh cleanup", "rendering", "plugin dev")
8. **Research context** — any existing research docs to copy in?
9. **Git + GitHub** — initialize repo and publish as private? (default: yes)
10. **MCP co-development?** — for native, desktop, graphics, AI, or CLI apps, scaffold an MCP server alongside the main app. Read the MCP co-development playbook from the active global playbook library for the full architecture pattern. Skip this for pure web apps where browser DevTools and web-fetching tools already give the agent enough visibility.
11. **Relevant playbooks?** — list the active global `playbooks/INDEX.md` entries whose `applies_to` overlaps the project's tech stack. Matching is case-insensitive substring: tokenize the user's tech stack (e.g., "Rust + cpal + egui + ZMQ" → tokens `rust`, `cpal`, `egui`, `zmq`), then surface every playbook where any token appears in the playbook's `applies_to` list or keywords. Show them to the user before scaffolding so they know what cross-project patterns are available. Examples: TensorRT for AI projects, Windows distribution for native Windows apps, ZMQ IPC for any IPC-using project.

## MCP Co-Development for Non-Web Apps

If the project is anything other than a pure web app, propose MCP co-development. Resolve the active playbook library in this order: `playbooks_path` from `.agents`, `.codex`, or `.claude` settings; then `~/.agents/playbooks/`; then `~/.codex/playbooks/`; then `~/.claude/playbooks/`. Read `mcp-co-development.md` before designing the architecture.

The pattern in one paragraph: a small Rust MCP server talks to the main app over ZeroMQ REQ/REP with JSON. The app exposes a state tree (universal control surface for parameters), an IPC bridge (command queue with main-thread safety), and a capture system (screenshots and texture readback). The MCP server provides ~7 multi-action tools. The agent uses this surface to test features as they ship.

When the project qualifies, the directory structure picks up:

```
{project-name}/
├── mcp-server-rs/              # Rust MCP server (cargo project)
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs             # MCP protocol handler over stdio
│       ├── ipc.rs              # ZMQ REQ client (Lazy Pirate timeout/reset)
│       └── tools/              # MCP tool implementations
│           ├── app.rs          # ping, launch, kill, status
│           ├── state.rs        # tree, get, set, list, invoke
│           └── capture.rs      # screenshots + texture readback
├── src/
│   └── automation/             # State tree + IPC bridge in main app
│       ├── state_tree.{cpp,h}  # path-addressed parameter tree
│       └── ipc_bridge.{cpp,h}  # ZMQ REP listener + command queue
└── .mcp.json                   # MCP server config (points at compiled binary)
```

Phase 1 of the implementation plan is always: build PING end-to-end, then state tree get/set, then capture, then UI tools. The playbook's "Development Loop" section spells out the order.

## Directory Structure to Create

```
{project-name}/
├── AGENTS.md                     # Lean cross-agent project instructions (~150 lines)
├── CLAUDE.md                     # Claude Code compatibility pointer or mirror
├── .gitignore                    # Language/framework-specific
├── .agents/
│   └── skills/                   # Canonical project-specific workflow skills
├── .claude/
│   └── skills/                   # Claude Code mirror when needed
├── .codex/
│   └── skills/                   # Codex mirror when needed
│       ├── {skill-1}/SKILL.md
│       └── {skill-2}/SKILL.md
├── docs/
│   ├── SCHEMA.md                 # Frontmatter contract (copied from bundle templates)
│   ├── implementation-plan.md    # Master roadmap with phase table
│   ├── state.md                  # Slim snapshot of current focus (updated by /end-session)
│   ├── lessons.md                # Gotchas accumulator (append-at-top, /end-session prompt)
│   ├── knowledge/                # Searchable topic-specific reference files
│   │   └── INDEX.md              # Master lookup table with keywords
│   ├── phases/                   # Detailed phase plans (one file per phase, with frontmatter)
│   ├── devlogs/                  # Daily development journals (YYYY-MM-DD-{topic}.md, with frontmatter)
│   ├── agent-learnings/          # Post-mortem analysis from significant sessions
│   ├── research_prompts/         # Research question documents
│   ├── research_results/         # Research findings and analysis
│   ├── reports/                  # Deep-dive technical reports
│   ├── design/                   # Architecture documents (spec.md from /spec-draft lands here)
│   └── strategy/                 # Strategic planning
├── {source-dirs}/                # Project-specific source code directories
├── scripts/                      # Utility scripts
├── tools/                        # Helper tools
└── reference/                    # Cloned repos for research (gitignored)
```

## Step-by-Step Workflow

### Step 1: Create Directory Structure

Create all directories. Use `.gitkeep` files in empty directories so git tracks them.

Copy these template files from the installed `scaffold-project/templates/` directory. Check `~/.agents/skills/`, `~/.codex/skills/`, and `~/.claude/skills/`, or use the bundle checkout if running from this repository:

- `templates/SCHEMA.md` → `docs/SCHEMA.md` (replace `__DATE__` with today)
- `templates/state-template.md` → `docs/state.md` (replace placeholders)
- `templates/lessons-template.md` → `docs/lessons.md` (replace `__DATE__`)

The `devlog-template.md`, `phase-template.md`, and `knowledge-template.md` stay in the bundle. `/end-session`, `/formalize-plan`, and the user create new instances of those by copying and customizing as work progresses.

### Step 2: Write AGENTS.md and CLAUDE.md

Follow this template for `AGENTS.md` — keep it lean (~150 lines). It's the agent's primary instruction file. Then create `CLAUDE.md` as a Claude Code compatibility mirror or short pointer to `AGENTS.md`; if the project already relies heavily on Claude Code, copying the same content into both files is acceptable.

```markdown
# Agent Instructions for {Project Name}

## Project Overview

{One paragraph description. What it is, what it does, why it exists.}

### Core Architecture
- **{Component 1}**: {description}
- **{Component 2}**: {description}
- ...

### Design Principles
1. **{Principle}** — {explanation}
2. ...

---

## Project Structure

{Directory tree showing the layout}

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| {component} | {tech} |
| ... | ... |

---

## Development Workflow

### Commit Message Format
```
<type>(<scope>): <description>
Types: feat, fix, docs, test, refactor, chore
```

---

## {Tool/API Surface} (if applicable)

| Tool | Actions |
|------|---------|
| ... | ... |

---

## Available Skills

| Skill | When to Use |
|-------|------------|
| ... | ... |

---

## Knowledge Base

Detailed reference in `docs/knowledge/` — see [INDEX.md](docs/knowledge/INDEX.md).

Search by keyword: `grep -rl "keyword" docs/knowledge/`

---

## Universal Rules (Apply to ALL Sessions)

1. **{Rule}** — {why it matters}
2. ...

---

## Related Projects

| Project | Path | Purpose |
|---------|------|---------|
| ... | ... | ... |

---

## Current Status

**Phase**: Phase 0 — Project Setup **Complete**

See [implementation-plan.md](docs/implementation-plan.md) for detailed roadmap.

---

## What to Avoid

### {Category}
- **{Anti-pattern}** — {why it's bad and what to do instead}
- ...
```

### Step 3: Write Implementation Plan

`docs/implementation-plan.md` — the master roadmap. Follow this structure:

```markdown
# {Project Name} Implementation Plan

## Overview
{What we're building and the key principle driving the architecture.}

## Architecture Principles
1. ...

## Phase Overview

| Phase | Focus | Status | Detailed Plan |
|-------|-------|--------|---------------|
| Phase 0 | Project Setup | **Complete** | This document |
| Phase 1 | {First real work} | **Planned** | [phase-1-{slug}.md](phases/phase-1-{slug}.md) |
| Phase 2 | {Next milestone} | **Planned** | [phase-2-{slug}.md](phases/phase-2-{slug}.md) |
| Phase 3 | {Future} | Unplanned | Create before starting |
| ... | ... | ... | ... |

---

## Phase 0: Project Setup (COMPLETE)

### Deliverables
- [x] Project folder structure
- [x] AGENTS.md and CLAUDE.md with project context
- [x] Implementation plan
- [x] Knowledge base seeded
- [x] Skill templates created
- [x] {Code skeleton items}
- [x] Git repository initialized

---

## Phase 1: {Title} (PLANNED)

{Detailed description with sub-phases, deliverables, key files, verification criteria.}

### Sub-phases

#### 1a: {First chunk}
- [ ] {deliverable}
- [ ] {deliverable}

#### 1b: {Second chunk}
- [ ] {deliverable}

### Key Files
- `path/to/file` — {description}

### Success Criteria
- [ ] {testable criterion}

---

## Phase 2: {Title} (PLANNED)
{Similar detail for Phase 2}

---

## Phase N: {Title} (UNPLANNED)
{Brief description of what this phase covers. Detail to be added before starting.}

---

## Design Decisions Log

### D1: {Decision Title}
**Decision**: {what was decided}
**Rationale**: {why}
```

**Rules for phases**:
- Phase 0 is always "Project Setup" and is always complete after scaffolding
- For MCP-co-developed projects, Phase 1 is always "MCP foundation": end-to-end PING, state tree get/set, basic capture
- First 1-2 phases should be fully detailed (sub-phases, deliverables, key files, success criteria)
- Later phases can be outlines — mark as "Unplanned"
- Each detailed phase gets its own file in `docs/phases/` with frontmatter per `docs/SCHEMA.md` (`type: phase`, `status: planned`, `phase_number`, `prerequisite`, `estimated_effort`, `summary`)

### Step 4: Write Phase Files

For each detailed phase, copy `templates/phase-template.md` to `docs/phases/phase-{N}-{slug}.md` and fill in placeholders. The template includes the proper YAML frontmatter (`type: phase`, `status`, `phase_number`, `prerequisite`, `estimated_effort`, `summary`) and section structure.

### Step 5: Create Knowledge Base

Create `docs/knowledge/INDEX.md`:

```markdown
---
type: knowledge-index
summary: Master lookup for all knowledge files in this project.
---

# Knowledge Base Index

Master lookup for all knowledge files. Each file has YAML frontmatter with `keywords: [a, b, c]`.

## Quick Answers

| Question | Answer | File |
|----------|--------|------|
| {common question} | {short answer} | `{file}.md` |

## File Directory

| File | Keywords | Description |
|------|----------|-------------|
| `{topic}.md` | {keyword1, keyword2} | {what it covers} |

## Search

`grep -rl "keyword" docs/knowledge/` for full-text search. `/lookup` skill greps frontmatter and INDEX together.
```

Each knowledge file uses `templates/knowledge-template.md` as its starting point. Includes proper frontmatter (`type: knowledge`, `keywords`, `related`, `summary`).

Create 3-5 initial knowledge files covering the project's core technical domains. Reference relevant playbooks in the `related:` field where applicable.

### Step 6: Create Skills

The workflow bundle's global skills (`/lookup`, `/start-session`, `/end-session`, `/checkpoint`, `/audit`, `/formalize-plan`, `/find-session`, `/slim-agent-md`, `/slim-claude-md`, `/research-prompt`, `/spec-draft`, `/scaffold-project`, `/extract-playbook`, `/audit-playbooks`) are already installed in the user's global agent skill directories and work in every project automatically. Do NOT re-create them inside the new project.

Create only project-specific skills here — skills tied to this project's domain that wouldn't make sense globally (e.g., "scaffold a new pipeline component", "build an engine pack", "render a test scene"). Put the canonical copy under `.agents/skills/<name>/SKILL.md`. Mirror to `.claude/skills/` and `.codex/skills/` only when the active agent needs its own discovery directory. Skip this step if the project doesn't need any project-specific skills yet; you can always add them later.

Each skill is a directory with a `SKILL.md`:

```markdown
---
name: {skill-name}
description: {one line}
user-invocable: true
---

# {Skill Title}

{What this skill does.}

## When to Use
- {trigger condition}

## Workflow

### Step 1: {action}
{details}

### Step 2: {action}
{details}

## Rules
1. {important constraint}
```

### Step 7: Create Code Skeleton

Based on the tech stack, create the minimal source code structure:
- Entry points with stub implementations
- Configuration files (package.json, pyproject.toml, Cargo.toml, etc.)
- Module/handler structure matching the planned tool/API surface
- Stub functions that raise `NotImplementedError` with the phase they'll be implemented in

The code should be **structurally complete but functionally empty** — all the wiring in place, no business logic.

For non-web projects answering "yes" to MCP co-development:
- Run `cargo new --bin mcp-server-rs` inside the project root and stub the IPC client + tool registry per the playbook's "Layer 3: The MCP Server (Rust)" section
- Stub `src/automation/state_tree.{cpp,h}` (or the language equivalent) with `setValue`, `getValue`, `listValues`, `invokeAction`
- Stub `src/automation/ipc_bridge.{cpp,h}` with a ZMQ REP socket and a handler map; register a `PING` handler that returns `{"status":"ok","msg":"pong"}`
- Add a `.mcp.json` at the project root pointing at the compiled `mcp-server-rs` binary
- Phase 1's first deliverable is end-to-end PING (agent → MCP server → ZMQ → app → response)

### Step 8: Write .gitignore

Language/framework-specific. Always include:
```
reference/
```

### Step 9: Git Init, Commit, and Publish

```bash
git init
git add -A
git commit -m "feat: Initial project scaffold — {Project Name}"
gh repo create {project-name} --private --source=. --push
```

## Rules

1. **AGENTS.md and CLAUDE.md stay lean** — ~150 lines max. Detailed reference goes in knowledge files, not the primary instruction files.
2. **Knowledge files have YAML frontmatter** — `type`, `keywords`, `related`, `summary` per `docs/SCHEMA.md`.
3. **Skills have YAML frontmatter** — `name`, `description`, `user-invocable: true`.
4. **Phase 0 is always complete** — the scaffolding IS Phase 0.
5. **Detail the first 1-2 phases fully** — sub-phases, deliverables, key files, success criteria. Later phases can be outlines.
6. **Code skeleton is structural, not functional** — stubs and wiring, no business logic.
7. **Every empty directory gets a `.gitkeep`** — so git tracks it.
8. **Copy relevant research** — if the user has existing research docs, copy them into the new project's research_prompts/ and research_results/.
9. **Design Decisions Log** — include in implementation-plan.md. Capture the "why" behind major architectural choices made during scaffolding.
10. **Match the user's domain** — knowledge files, skills, and code structure should reflect the actual project, not be generic boilerplate.
11. **For MCP-co-developed projects, automation is Phase 1** — never push it later. The playbook's argument is that automation built early shapes the whole app; automation bolted on after the fact fights the app's assumptions.
12. **Frontmatter contract is non-optional** — `docs/SCHEMA.md` ships with every project. Devlogs, phase docs, knowledge files, lessons, state, spec all use it. Skills like `/start-session`, `/end-session`, `/find-session`, `/audit` query frontmatter via grep.
13. **Adopt the bundle's templates** — copy from the installed `scaffold-project/templates/` into the new project. Don't re-invent format conventions.
14. **Surface relevant playbooks early** — read the active global `playbooks/INDEX.md` and tell the user which patterns apply to their stack. Saves them from re-deriving.

## What NOT to Do

- Don't write actual business logic — this is scaffolding, not implementation
- Don't create a README.md — AGENTS.md serves this purpose for agent-driven projects
- Don't over-engineer the code skeleton — minimal stubs that show the architecture
- Don't add skills that aren't relevant — only create skills for workflows the project actually needs
- Don't skip the implementation plan — it's the backbone of the entire development system
- Don't make AGENTS.md or CLAUDE.md a wall of text — keep it scannable, link out to knowledge files for depth
- Don't ship MCP co-development for projects that don't need it. Pure web apps, single-file scripts, and read-only tools rarely benefit. The cost is real (extra Rust crate, ZMQ dependency, command queue plumbing).
