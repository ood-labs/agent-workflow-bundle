---
name: find-session
description: Find and inspect previous Claude Code or Codex session transcripts
allowed-tools: Glob, Grep, Read, Bash(powershell:*), Bash(ls:*)
user-invocable: true
---

Find previous agent session transcripts. Claude Code sessions are stored as JSONL files at:

- Windows: `%USERPROFILE%\.claude\projects\<project-key>\<session-id>.jsonl`
- macOS / Linux: `~/.claude/projects/<project-key>/<session-id>.jsonl`

Codex sessions are commonly stored under:

- Windows: `%USERPROFILE%\.codex\sessions\`
- macOS / Linux: `~/.codex/sessions/`

The project key is the working directory path with separators replaced by `--` (e.g., `C--Users-<user>-Documents-dev-pulse` on Windows, or similar on Mac/Linux).

## Steps

1. **Detect OS.** Resolve the absolute path for the projects directory:
   - Windows (PowerShell): `$env:USERPROFILE\.claude\projects\` and `$env:USERPROFILE\.codex\sessions\`
   - macOS / Linux: `~/.claude/projects/` and `~/.codex/sessions/`

2. **Identify the project**: If the user specifies a project path or name, convert it to the project key format. If not specified, use the current working directory. Use Glob to verify the project directory exists.

3. **List recent sessions**: run the OS-appropriate command. Replace `<project-key>` with the resolved key from Step 2.

   PowerShell (Windows):
   ```
   powershell -c "Get-ChildItem \"$env:USERPROFILE\.claude\projects\<project-key>\*.jsonl\" | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | Format-Table Name, LastWriteTime, @{N='Size';E={if($_.Length -gt 1MB){'{0:N1} MB' -f ($_.Length/1MB)}else{'{0:N0} KB' -f ($_.Length/1KB)}}} -AutoSize"
   ```

   Bash (macOS / Linux):
   ```
   ls -lt ~/.claude/projects/<project-key>/*.jsonl | head -10
   ```

4. **Show session summary**: for each session the user is interested in, read the first few lines to get the opening user message (shows what the session was about), and read the last ~15 lines to see where it left off.

5. **Parse the JSONL**: each line is a JSON object. Key fields:
   - `type`: "user", "assistant", "system", "progress"
   - `message.content`: the actual message text (for user/assistant types)
   - `timestamp`: when the message was sent
   - `slug`: the session's human-readable name
   - Look for `"[Request interrupted by user]"` to detect if the session was cancelled mid-response

6. **Present findings clearly**: tell the user:
   - When the session started and ended (timestamps from first and last messages)
   - The session slug/name if available
   - What the session was about (first user message summary)
   - Where it left off (last assistant message + last user response)
   - Whether it ended cleanly or was interrupted

## Arguments

If the user provides arguments like a project name or path, use that to find the right project directory. Otherwise default to the current project.
