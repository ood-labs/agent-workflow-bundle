# Install Instructions

This document tells an agent how to install the Agent Workflow Bundle into one or more global agent configuration directories.

## Target paths

| Target | Windows root | macOS / Linux root | Skills directory | Playbooks directory |
|--------|--------------|--------------------|------------------|---------------------|
| Agent-neutral | `%USERPROFILE%\.agents\` | `~/.agents/` | `<root>/skills/` | `<root>/playbooks/` |
| Claude Code | `%USERPROFILE%\.claude\` | `~/.claude/` | `<root>/skills/` | `<root>/playbooks/` |
| Codex | `%USERPROFILE%\.codex\` | `~/.codex/` | `<root>/skills/` | `<root>/playbooks/` |

Install to `.agents` for the portable canonical copy, and mirror to `.claude` and `.codex` when those agents need their own discovery path.

## Preferred install

PowerShell:

```powershell
.\scripts\install.ps1 -Target all
```

Bash:

```bash
chmod +x scripts/*.sh
./scripts/install.sh all
```

OS-named Unix wrappers:

```bash
./scripts/install-macos.sh all
./scripts/install-linux.sh all
```

Valid targets are `agents`, `claude`, `codex`, and `all`. The scripts create missing directories, copy every `skills/<skill-name>/` folder as a whole subtree, and copy every file in `playbooks/`.

The scripts do not silently overwrite existing skills or playbooks. Use `-Overwrite` in PowerShell or `OVERWRITE=1` in Bash only after checking conflicts.

## Manual install

1. Detect the OS and resolve the root directory for each requested target.
2. Create `<root>/skills/` and `<root>/playbooks/` if missing.
3. Check for conflicts before copying. For each subfolder in `skills/` and each file in `playbooks/`, check whether the same name already exists at the target. If it does, list the conflicts and ask whether to overwrite, skip, or rename.
4. Copy skills. Each `skills/<skill-name>/` folder copies as a whole subtree to `<root>/skills/<skill-name>/`. The `skills/scaffold-project/templates/` folder travels with the skill.
5. Copy playbooks. Each file in `playbooks/`, including `INDEX.md`, copies to `<root>/playbooks/`. If `INDEX.md` already exists, merge manually instead of overwriting without review.
6. Confirm the installed skills, playbooks, and target paths.

## Runtime path resolution

Skills that read the global playbook library should resolve paths in this order:

1. `playbooks_path` in the active agent settings file, if present.
2. `~/.agents/playbooks/`
3. `~/.codex/playbooks/`
4. `~/.claude/playbooks/`

Settings files to check:

- Windows: `%USERPROFILE%\.agents\settings.json`, `%USERPROFILE%\.codex\settings.json`, `%USERPROFILE%\.claude\settings.json`
- macOS / Linux: `~/.agents/settings.json`, `~/.codex/settings.json`, `~/.claude/settings.json`

Example:

```json
{
  "playbooks_path": "/absolute/path/to/playbooks"
}
```

## What NOT to install

The following stay in the bundle folder:

- `README.md`: for the user to read about the bundle
- `INSTALL.md`: this file
- `WORKFLOW.md`: the workflow narrative
- `example-skeleton/`: illustrative example of what `/scaffold-project` produces
- `scripts/`: installer helpers

## Verifying

After install, list the contents of the target directories and confirm:

- Each skill folder is present at `<root>/skills/`
- `<root>/playbooks/INDEX.md` exists and lists every playbook file present
- `<root>/skills/scaffold-project/templates/` has `SCHEMA.md` and 5 template files

If an agent is already running in another window, restart it if newly installed skills do not appear immediately.
