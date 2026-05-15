# Knowledge Base Index

Master lookup for all knowledge files. Each file has `<!-- keywords: ... -->` on line 2.

## Quick Answers

| Question | Answer | File |
|----------|--------|------|
| Where do parameters live? | In the state tree at `/app/...` paths | `state-tree.md` |
| How does the agent test features? | Through MCP tools that drive the state tree | `mcp-tools.md` |

## File Directory

| File | Keywords | Description |
|------|----------|-------------|
| `state-tree.md` | state, parameters, registry, ui, persistence | How the state tree works and how to register parameters |
| `mcp-tools.md` | mcp, automation, ipc, tools, zmq | The MCP tool surface and how to extend it |

## Search

```bash
grep -rl "keyword" docs/knowledge/
```

## How to add an entry

1. Create `docs/knowledge/<topic>.md`
2. Line 1: `# <Topic> Reference`
3. Line 2: `<!-- keywords: comma, separated, tags -->`
4. Body: organized by subtopic with tables, code blocks, and concrete examples
5. Add a row to the File Directory table above
