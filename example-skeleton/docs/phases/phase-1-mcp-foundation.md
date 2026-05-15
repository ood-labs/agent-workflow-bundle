---
type: phase
status: planned
phase_number: "1"
prerequisite: Phase 0 complete
estimated_effort: 5-7 days
summary: Prove the MCP automation surface works end-to-end before any feature work.
note_created: 2026-05-08
updated: 2026-05-08
---

# Phase 1: MCP Foundation

## Goal

Prove the automation surface works end-to-end before any feature work. By the end of this phase, the agent can launch the app, ping it, read the state tree, set a parameter, and capture a screenshot — all through the MCP server.

## Sub-phases

### 1a: PING end-to-end

**Deliverables**:
- [ ] App opens a ZMQ REP socket on `tcp://127.0.0.1:5555`
- [ ] App handles `{"cmd": "PING"}` returning `{"status": "ok", "msg": "pong"}`
- [ ] MCP server `app` tool with `ping` action sends PING and reports the response
- [ ] The agent can invoke `app ping` and get pong back

**Technical Details**:

App side (`src/automation/ipc_bridge.cpp`): start a thread that owns the ZMQ REP socket. On incoming message, parse JSON, dispatch by `cmd` field. PING runs on the listener thread (no main-thread queue needed for read-only commands).

MCP server (`mcp-server-rs/src/tools/app.rs`): expose `app` tool with action enum. `ping` action sends `{"cmd": "PING"}` over the ZMQ REQ socket and returns the response.

**Verification**: launch the app, run `claude` in another window, invoke the MCP tool, see `pong`.

---

### 1b: State tree get / set

**Deliverables**:
- [ ] `StateTree` class with `setValue`, `getValue`, `listValues`, `getSubtree`
- [ ] At least three test parameters registered (one float, one int, one bool)
- [ ] App handles `GET_STATE_VALUE`, `SET_STATE_VALUE`, `LIST_STATE_VALUES`, `GET_STATE_TREE`
- [ ] `state` MCP tool with `get`, `set`, `list_values`, `tree` actions
- [ ] Setters and getters protected by `shared_mutex`

**Verification**: The agent reads the state tree, sets a parameter, reads back the new value.

---

### 1c: Screenshot capture

**Deliverables**:
- [ ] App handles `CAPTURE_SCREENSHOT` returning a base64-encoded PNG of the main window
- [ ] `capture` MCP tool with `screenshot` action
- [ ] Window capture uses GDI on Windows; equivalent on macOS or Linux

**Verification**: The agent captures the app window, sees the rendered output as an image.

## Key Files

| File | Status | Description |
|------|--------|-------------|
| `src/automation/state_tree.h` | Modify | Add `setValue`, `getValue`, `listValues` |
| `src/automation/state_tree.cpp` | Modify | Implement with `shared_mutex` |
| `src/automation/ipc_bridge.cpp` | Modify | ZMQ listener thread + handler map |
| `mcp-server-rs/src/tools/app.rs` | Modify | `ping` action |
| `mcp-server-rs/src/tools/state.rs` | New | `get`, `set`, `list_values`, `tree` actions |
| `mcp-server-rs/src/tools/capture.rs` | New | `screenshot` action |

## Success Criteria

- [ ] The agent can drive the entire surface from a Codex or Claude Code session
- [ ] PING round-trip latency under 5ms
- [ ] State tree access is thread-safe under concurrent UI and MCP load
- [ ] Screenshot capture works on the target OS
