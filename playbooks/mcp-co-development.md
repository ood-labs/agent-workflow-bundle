---
type: playbook
name: mcp-co-development
keywords: [mcp, automation, ipc, zmq, state-tree, capture, rust, native-app]
applies_to: [native-app, desktop, graphics, ai, cli-tool]
last_verified: 2026-05-08
verified_against: Sentinel v0.3.9.8 (Rust MCP server, ZeroMQ REQ/REP, ImGui, CUDA)
summary: Architecture pattern for building a native app and its Rust MCP server in lockstep. Three layers: state tree, ZMQ IPC bridge, multi-action MCP tools.
---

# MCP Co-Development Playbook

How to build an application and its MCP server simultaneously so that the agent can test, verify, and eventually automate the entire system end-to-end. Based on the Sentinel project's architecture.

---

## The Core Idea

Most MCP integrations are bolted on after the fact — someone writes an app, then writes a separate MCP server that pokes at it through whatever API happens to exist. This works, but it's fragile. The API wasn't designed for automation, the MCP server fights the app's assumptions, and the agent ends up working through a keyhole.

The alternative: **build both at the same time**. Design the app from day one with an automation surface that the MCP server can use. The MCP server isn't an afterthought — it's how you test the app during development. The agent uses it to verify features as they're built, catch regressions, and eventually orchestrate complex workflows that would be tedious to do manually.

The result is an app that's deeply automatable because automation was a first-class concern from the start, and an MCP server that's reliable because it was tested against real app behavior throughout development.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  Agent (via MCP protocol)                           │
│  - Calls tools to control the app                    │
│  - Takes screenshots to verify UI state              │
│  - Captures output to verify processing results      │
│  - Reads state tree to understand current config     │
└────────────────┬─────────────────────────────────────┘
                 │ MCP protocol (stdio)
┌────────────────▼─────────────────────────────────────┐
│  MCP Server (Rust binary, ~2MB)                      │
│  - 7 multi-action tools                              │
│  - Translates MCP calls → IPC commands               │
│  - Handles screenshots via OS APIs                   │
│  - Manages app lifecycle (launch/kill)               │
└────────────────┬─────────────────────────────────────┘
                 │ ZeroMQ REQ/REP (JSON over TCP)
┌────────────────▼─────────────────────────────────────┐
│  Application (C++ executable)                        │
│  - AutomationBridge: ZMQ listener + command dispatch │
│  - StateTree: universal parameter control surface    │
│  - Capture: GPU texture readback to PNG              │
│  - UI introspection: window/widget enumeration       │
└──────────────────────────────────────────────────────┘
```

Three layers, two boundaries, one JSON protocol.

---

## Layer 1: The State Tree (App Side)

This is the single most important design decision. Every controllable value in the application lives in a hierarchical, path-addressed state tree — like a filesystem for parameters.

### What It Looks Like

```
/app/
  pipelines/
    pipeline_0/
      parameters/
        brightness    (float, 0.0-1.0, default 0.5)
        mode          (enum: ["fast", "quality", "balanced"])
        enabled       (bool, default true)
      actions/
        relaunch      (callable, no args)
        export        (callable, args: {path: string})
  sources/
    webcam_0/
      parameters/
        resolution    (enum: ["720p", "1080p", "4k"])
  settings/
    output_fps       (int, 1-120, default 30)
```

### Why This Matters

The state tree is the **universal control surface**. It serves four roles simultaneously:

1. **MCP automation** — the agent reads and writes parameters by path
2. **UI binding** — the GUI reads from and writes to the same tree
3. **OSC/external control** — OSC addresses map directly to tree paths
4. **Project serialization** — save/load is just serialize/deserialize the tree

One source of truth. No sync bugs. When the agent sets `/app/pipelines/pipeline_0/parameters/brightness` to `0.7`, the UI slider moves, the processing pipeline updates, and if the project is saved, that value persists. There's no special "automation mode" — the same mechanism that the UI uses is what automation uses.

### Design Rules for the State Tree

- **Every user-facing parameter** gets a node. If a user can change it in the UI, it must be in the tree.
- **Typed values with metadata**: min, max, default, read-only flag, enum options. This lets the agent discover valid ranges without documentation.
- **Actions are tree nodes too**: Not just data — callable operations like "relaunch" or "export" live in the tree alongside parameters. `invoke("/app/pipelines/p0/actions/relaunch")` is just another tree operation.
- **Thread-safe access**: The tree must handle concurrent reads/writes from the UI thread, automation thread, and any worker threads. Use a shared mutex.
- **Introspectable**: `list_values("/app/pipelines/p0/parameters")` returns all parameter paths. `get("/path")` returns value + type + metadata. The agent can explore the tree without documentation.

### Implementation Sketch (C++)

```cpp
class StateTree {
public:
    static StateTree& instance();  // singleton

    // Values
    void setValue(const std::string& path, const std::string& value);
    std::string getValue(const std::string& path) const;
    json getSubtree(const std::string& path) const;  // recursive
    std::vector<std::string> listValues(const std::string& path) const;

    // Actions
    json invokeAction(const std::string& path, const json& args);
    std::vector<std::string> listActions(const std::string& path) const;

    // Registration (called during initialization)
    void registerValue(const std::string& path, ValueNode node);
    void registerAction(const std::string& path, ActionHandler handler);

    // Serialization
    json serializePersistent() const;
    void deserializePersistent(const json& data);

private:
    mutable std::shared_mutex m_mutex;
    // tree structure...
};
```

Each component registers its parameters during initialization:

```cpp
void MyPipeline::initialize() {
    auto& tree = StateTree::instance();
    std::string base = "/app/pipelines/" + m_id + "/parameters/";

    tree.registerValue(base + "brightness", {
        .type = ValueType::Float,
        .min = 0.0f, .max = 1.0f, .default_ = 0.5f,
        .getter = [this]() { return std::to_string(m_brightness); },
        .setter = [this](const std::string& v) { m_brightness = std::stof(v); }
    });
}
```

---

## Layer 2: The IPC Bridge (App Side)

The app needs a way to receive commands from the outside world. This is a thin layer that listens on a socket, dispatches commands to handlers, and returns results.

### Transport: ZeroMQ REQ/REP

ZeroMQ with the REQ/REP pattern is the sweet spot:

- **Simple**: Request in, response out. No streaming, no callbacks, no connection management.
- **Reliable**: Built-in message framing, reconnection, buffering.
- **Fast**: Sub-millisecond latency on localhost. No HTTP overhead.
- **Cross-language**: C/C++/Rust/Python bindings all mature.
- **Debuggable**: JSON payloads are human-readable in any ZMQ monitoring tool.

```
MCP Server (Rust)         App (C++)
   REQ socket ──────────── REP socket
              tcp://127.0.0.1:5555
```

### Message Format

Keep it dead simple — JSON objects with a `cmd` field:

```json
// Request
{"cmd": "SET_STATE_VALUE", "path": "/app/pipelines/p0/parameters/brightness", "value": "0.7"}

// Response (success)
{"status": "ok", "data": {"path": "...", "value": "0.7", "type": "float"}}

// Response (error)
{"status": "error", "msg": "path not found: /app/pipelines/p0/parameters/typo"}
```

No protobuf, no msgpack, no versioned schemas. JSON is good enough for automation IPC and it's directly readable in logs.

### Thread Safety: The Command Queue

Most apps have a main thread that owns the UI and GPU resources. You can't safely mutate state from the ZMQ listener thread. Solution: a promise-based command queue.

```
ZMQ Listener Thread                    Main Thread (each frame)
─────────────────                      ────────────────────────
1. Receive request                     
2. Parse JSON                          
3. Is this a main-thread command?      
   YES → queue with promise            → processCommands()
         wait on future (60s timeout)     dequeue, execute handler
                                          set promise value
   ← get result from future            
4. Send response                       
                                       
   NO → execute immediately            
        send response                  
```

Some commands (like PING) don't touch shared state and can run on the listener thread directly. Everything else gets queued. The 60-second timeout prevents the listener from hanging forever if the main thread is stuck.

### Handler Registration

Use a simple map from command name to handler function:

```cpp
class AutomationBridge {
    std::unordered_map<std::string, std::function<json(const json&)>> m_handlers;

    void registerHandler(const std::string& cmd, std::function<json(const json&)> handler) {
        m_handlers[cmd] = std::move(handler);
    }
};

// During initialization
bridge.registerHandler("SET_STATE_VALUE", [](const json& req) {
    auto path = req.at("path").get<std::string>();
    auto value = req.at("value").get<std::string>();
    StateTree::instance().setValue(path, value);
    return json{{"status", "ok"}};
});
```

This is deliberately simple. No middleware, no interceptors, no plugin system. A map of functions.

---

## Layer 3: The MCP Server (Rust)

The MCP server is a separate binary that speaks MCP protocol on stdio and IPC to the app via ZeroMQ. It translates between the two worlds.

### Why a Separate Binary

- **Language freedom**: Write it in Rust for reliability and easy distribution (~2MB static binary). The app can be C++, C#, Python, whatever.
- **Crash isolation**: If the MCP server crashes, the app keeps running. If the app crashes, the MCP server can detect it and report the error.
- **Independent deployment**: Update the MCP server without rebuilding the app and vice versa.
- **Startup independence**: The MCP server can launch the app, or connect to an already-running instance.

### Tool Design: Few Tools, Many Actions

Instead of 50 single-purpose MCP tools, use ~7 multi-action tools. Each tool takes an `action` parameter that selects the operation:

```json
// One tool, many operations
{"tool": "app_state", "action": "get", "path": "/app/pipelines/p0/parameters/brightness"}
{"tool": "app_state", "action": "set", "path": "...", "value": "0.7"}
{"tool": "app_state", "action": "tree", "path": "/app/pipelines"}
{"tool": "app_state", "action": "list_values", "path": "/app/pipelines/p0"}
{"tool": "app_state", "action": "invoke", "path": "/app/pipelines/p0/actions/relaunch"}
```

Why this works better:

- **Reduced cognitive load**: the agent sees 7 tools, not 50. Each tool is a coherent domain.
- **Natural grouping**: All state operations together, all pipeline operations together, all capture operations together.
- **Stable interface**: Adding a new action to an existing tool doesn't change the tool list.
- **Better descriptions**: One good description per domain vs. 50 terse one-liners.

Recommended tool grouping:

| Tool | Domain | Actions |
|------|--------|---------|
| `app` | Lifecycle | ping, launch, kill, status, logs, diagnostic |
| `state` | Parameters | tree, get, set, list_values, list_actions, invoke |
| `pipeline` | Processing units | list, create, destroy, info, set_input, configure |
| `graph` | Topology/routing | get, add_link, remove_link, auto_layout |
| `capture` | Visual output | source, pipeline, region |
| `screenshot` | UI verification | window, element |
| `ui` | UI interaction | get_tree, click, set, send_key |

### IPC Client Pattern (Rust)

The MCP server maintains a ZMQ REQ socket to the app. Use the "Lazy Pirate" pattern — reset the socket on timeout to clear stale protocol state:

```rust
pub struct IpcClient {
    ctx: zmq::Context,
    socket: zmq::Socket,
    endpoint: String,
    timeout: Duration,
}

impl IpcClient {
    pub async fn send_command(&mut self, cmd: &str, params: Value) -> Result<Value> {
        let request = json!({"cmd": cmd, ..params});
        let msg = serde_json::to_string(&request)?;

        // Send with timeout
        self.socket.send(&msg, 0)
            .map_err(|_| anyhow!("send timeout"))?;

        // Receive with timeout (poll first)
        if self.socket.poll(zmq::POLLIN, self.timeout.as_millis() as i64)? == 0 {
            self.reset_socket()?;  // Lazy Pirate: reset on timeout
            return Err(anyhow!("response timeout"));
        }

        let response = self.socket.recv_string(0)??;
        let parsed: Value = serde_json::from_str(&response)?;

        if parsed["status"] == "error" {
            return Err(anyhow!("{}", parsed["msg"]));
        }

        Ok(parsed)
    }
}
```

---

## The Capture System

This is what makes the architecture truly powerful for the agent. Without visual feedback, the agent is flying blind — it can set parameters but can't verify the result. The capture system closes the loop.

### Two Kinds of Capture

**Screenshots** (OS-level, what the user sees):
- Capture the application window via OS APIs (GDI on Windows, screencapture on macOS)
- Crop to specific UI panels by querying the UI tree for element bounds
- Returns base64-encoded image directly in MCP response
- Used for: verifying UI state, reading error messages, checking layout

**Texture Capture** (GPU-level, what the app produces):
- Read back GPU textures (processing output, source input) to CPU
- Stage through a CPU-readable buffer, save as PNG
- Returns file path (too large for inline base64 in most cases)
- Used for: verifying processing results, comparing output quality, debugging visual artifacts

### Why Both Matter

Screenshots tell the agent "the UI is showing the right controls." Texture capture tells the agent "the processing pipeline is producing the right output." Together, they let the agent verify the entire system end-to-end — from parameter change to visual result.

```
The agent sets denoise=0.7
  → verifies via state tree: value accepted ✓
  → takes screenshot: UI slider moved ✓
  → captures output texture: image looks correct ✓
```

This is the difference between "I set the parameter" and "I confirmed it actually worked."

---

## The Development Loop

Here's how this architecture changes the development workflow:

### Phase 1: Foundation (Week 1-2)

Build the minimum viable automation surface:

1. **State tree skeleton** — register a handful of parameters, even if they don't do anything yet
2. **ZMQ listener** — accept commands, dispatch to handlers, return JSON
3. **MCP server** — connect to app, expose state tool with get/set/tree actions
4. **PING command** — the simplest possible end-to-end test

At this point the agent can: launch the app, ping it, read the state tree, set parameters. That's enough to start testing.

### Phase 2: Feature Development (Ongoing)

For every feature you build:

1. **Register parameters in the state tree** — before building the UI
2. **Build the processing logic** — verify via MCP parameter setting + texture capture
3. **Build the UI** — verify via MCP screenshots
4. **Add any needed IPC commands** — if the feature needs operations beyond get/set (creation, destruction, complex actions)

The agent tests each layer as it's built. By the time the UI exists, the automation path is already working.

### Phase 3: Automation Scripts (When Stable)

Once the MCP surface is solid, the agent can orchestrate complex workflows:

- "Create a pipeline, connect this source, set these parameters, verify the output looks correct"
- "Load this project, change the resolution, re-verify all outputs"
- "Run through every parameter combination and capture output for each"

These aren't brittle UI-click scripts. They're operating on the same stable state tree that the UI uses. If you redesign the UI, the automation still works.

---

## Why This Works So Well

### 1. Single Source of Truth

The state tree eliminates the "two APIs" problem. The UI and automation use the same mechanism. There's no drift between "what the UI can do" and "what automation can do" because they're the same thing.

### 2. Introspectable by Design

The agent can call `state tree` to see every parameter in the system, with types, ranges, and current values. It doesn't need documentation — it can explore. When you add a new parameter, the agent can discover it immediately.

### 3. Visual Verification Closes the Loop

Setting a value and hoping it worked is fragile. Screenshots and texture capture let the agent verify results visually. This is especially important for media/graphics applications where "did it work" is a visual question.

### 4. Crash Isolation

The MCP server and app are separate processes. If the app crashes during testing, the MCP server detects it, reports the error, and can relaunch. The agent gets a clean error instead of a hung connection.

### 5. No Special Automation Mode

The app doesn't know or care whether a command came from the UI, OSC, or MCP. There's no "test mode" or "automation flag." This means automation tests real behavior, not a simulated subset.

### 6. Incremental Adoption

You don't have to automate everything on day one. Start with PING + state get/set. Add capture when you need visual verification. Add UI interaction when you need to test UI-specific behavior. Each layer is independently useful.

---

## Practical Decisions

### ZeroMQ vs. Alternatives

| Option | Verdict | Why |
|--------|---------|-----|
| **ZeroMQ REQ/REP** | Recommended | Simple, reliable, cross-language, sub-ms latency |
| HTTP/REST | Viable but heavier | More overhead, more dependencies, but easier to debug with curl |
| gRPC | Overkill | Schema management overhead not worth it for local IPC |
| Named pipes | Platform-specific | Works but ZMQ abstracts this better |
| Shared memory | Too low-level | Fast but complex synchronization |
| stdin/stdout | Fragile | No reconnection, buffering issues, one client only |

### MCP Server Language

Rust is ideal — single static binary, tiny footprint, excellent ZMQ/JSON support, no runtime dependencies. But any language works. The MCP server is simple enough that language choice matters less than getting the IPC protocol right.

### JSON vs. Binary Protocol

JSON. Always JSON for this use case. The messages are small (< 1KB typically), the overhead is negligible on localhost, and the debuggability is invaluable. When you're staring at ZMQ logs trying to figure out why a command failed, you want to read the payload.

### How Many Tools

Aim for 5-10 multi-action tools. Fewer than 5 means each tool is doing too many unrelated things. More than 15 means the agent's tool selection gets noisy. Group by domain, not by operation.

---

## Checklist for New Projects

### App Side

- [ ] State tree with typed, metadata-rich parameter nodes
- [ ] State tree actions for operations beyond get/set
- [ ] ZMQ REP socket on a configurable port (default 5555)
- [ ] JSON command protocol: `{cmd, ...params}` → `{status, data/msg}`
- [ ] Command queue for main-thread safety
- [ ] PING handler (minimum viable automation)
- [ ] State handlers: GET_TREE, GET_VALUE, SET_VALUE, LIST_VALUES, LIST_ACTIONS, INVOKE_ACTION
- [ ] Capture handler: read back output to PNG
- [ ] Conditional compilation flag (e.g., `-DENABLE_AUTOMATION`) to strip from production if needed

### MCP Server Side

- [ ] ZMQ REQ client with Lazy Pirate timeout/reset
- [ ] App lifecycle management (launch, kill, ping, status)
- [ ] State tool (tree, get, set, list_values, list_actions, invoke)
- [ ] Capture tool (output textures → PNG → file path or base64)
- [ ] Screenshot tool (window capture via OS APIs)
- [ ] Sensible timeouts (5s default, 60s for heavy operations)
- [ ] Error propagation: IPC errors → MCP tool errors with context

### Development Process

- [ ] PING works end-to-end before building anything else
- [ ] Every new parameter registered in state tree before UI work
- [ ] The agent tests each feature via MCP as it's built
- [ ] Screenshot captures used to verify UI changes
- [ ] Output captures used to verify processing changes

---

## End-to-End Example: Adding a "Blur" Feature

Here's what the workflow looks like in practice:

**Step 1**: Register the parameter

```cpp
tree.registerValue(base + "blur_radius", {
    .type = ValueType::Float,
    .min = 0.0f, .max = 20.0f, .default_ = 0.0f,
    .getter = [this]() { return std::to_string(m_blurRadius); },
    .setter = [this](const std::string& v) { m_blurRadius = std::stof(v); }
});
```

The agent can immediately discover and set this parameter via MCP, even before the UI exists.

**Step 2**: Build the processing logic

```cpp
if (m_blurRadius > 0.0f) {
    applyGaussianBlur(input, output, m_blurRadius);
}
```

The agent sets `blur_radius=5.0`, captures the output texture, and verifies the image is blurred.

**Step 3**: Build the UI

```cpp
ImGui::SliderFloat("Blur", &m_blurRadius, 0.0f, 20.0f);
// (StateTree binding handles sync)
```

The agent takes a screenshot, verifies the slider appears, sets the value via MCP, takes another screenshot to confirm the slider moved.

**Step 4**: Edge cases

The agent tests `blur_radius=0` (should be passthrough), `blur_radius=20` (maximum), rapid changes, interaction with other parameters. All automated, all verified visually.

The feature is tested end-to-end before a human ever touches it.

---

## Summary

Build the state tree first. Add IPC early. Write the MCP server alongside the app. Test with the agent as you go. By the time the app is feature-complete, you have a battle-tested automation surface that the agent can use to orchestrate anything the app can do — because automation was never an afterthought, it was the development methodology.


