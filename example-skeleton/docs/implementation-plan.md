# ExampleApp Implementation Plan

## Overview

A native desktop image processing tool with a GPU compute backend, Dear ImGui frontend, and Rust MCP server for end-to-end automation. The architecture treats automation as a first-class concern: every parameter lives in a state tree that the UI, MCP server, and project save/load all share.

## Architecture Principles

1. **State tree is the universal control surface** — single source of truth for every parameter
2. **Automation built early, not late** — Phase 1 is end-to-end MCP, before any features
3. **GPU-first** — keep pixels on the GPU; round-trip to CPU only for saves and screenshots
4. **Crash-isolated MCP** — MCP server is a separate Rust binary, not in-process

## Phase Overview

| Phase | Focus | Status | Detailed Plan |
|-------|-------|--------|---------------|
| Phase 0 | Project Setup | **Complete** | This document |
| Phase 1 | MCP Foundation | **Planned** | [phase-1-mcp-foundation.md](phases/phase-1-mcp-foundation.md) |
| Phase 2 | Image Pipeline | Unplanned | Create before starting |
| Phase 3 | UI | Unplanned | Create before starting |
| Phase 4 | Project Save / Load | Unplanned | Create before starting |

---

## Phase 0: Project Setup (COMPLETE)

### Deliverables
- [x] Project folder structure
- [x] AGENTS.md and CLAUDE.md with project context
- [x] Implementation plan
- [x] Knowledge base seeded
- [x] App source skeleton (state_tree, ipc_bridge stubs)
- [x] Rust MCP server skeleton (ipc, tool registry stubs)
- [x] `.mcp.json` pointing at MCP server binary
- [x] Git repository initialized

---

## Phase 1: MCP Foundation (PLANNED)

End-to-end PING, then state tree get/set, then capture. No features yet — this phase exists to prove the automation surface works before any product decisions are made.

See [phase-1-mcp-foundation.md](phases/phase-1-mcp-foundation.md) for detailed sub-phases.

---

## Phase 2: Image Pipeline (UNPLANNED)

Once the MCP foundation is solid, build the GPU compute backend. Each filter registers its parameters in the state tree before the UI exists, so the agent can drive it from MCP.

---

## Phase 3: UI (UNPLANNED)

Dear ImGui frontend bound to the state tree. Sliders, dropdowns, and toggles read and write the same nodes that MCP commands hit.

---

## Phase 4: Project Save / Load (UNPLANNED)

Serialize and deserialize the persistent subset of the state tree. JSON format. Versioning strategy TBD.

---

## Design Decisions Log

### D1: Rust for the MCP server
**Decision**: Build the MCP server in Rust as a separate binary, not in-process with the C++ app.
**Rationale**: Single static binary for distribution, crash isolation from the app, mature ZMQ and JSON crates, no need to entangle the app's build system with MCP protocol concerns.

### D2: ZeroMQ REQ/REP over HTTP
**Decision**: Use ZMQ REQ/REP with JSON payloads for app-to-MCP IPC.
**Rationale**: Sub-millisecond latency on localhost, automatic reconnection, no HTTP overhead, debuggable with any ZMQ monitoring tool.

### D3: Few tools, many actions
**Decision**: ~7 multi-action MCP tools rather than dozens of single-purpose tools.
**Rationale**: Reduces agent cognitive load when picking a tool, groups related operations naturally, keeps the tool list stable as the app grows.
