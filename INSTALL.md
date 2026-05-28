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

## Updating an installed bundle

Updates use the same installer with the `-Overwrite` / `OVERWRITE=1` flag. The flag is destructive — it deletes each installed skill subtree before copying the new one — so follow the steps in order rather than running the installer directly.

### 1. Refresh the bundle source

If the bundle is a git clone:

```powershell
cd <bundle-path>
git fetch origin
git status            # confirm nothing local you'd lose
git pull --ff-only
```

If you grabbed the bundle as a download, replace your local copy with the new release tarball/zip before continuing.

### 2. Preview the changes (dry-run)

Run the installer with both `-DryRun` and `-Overwrite`. This lists every skill subtree and playbook file that would be replaced, without writing anything:

PowerShell:

```powershell
.\scripts\install.ps1 -Target all -DryRun -Overwrite
```

Bash:

```bash
DRY_RUN=1 OVERWRITE=1 ./scripts/install.sh all
```

Read the output. Anything you don't recognize as an intended upstream change is worth investigating before the real run.

### 3. Back up customizations you want to keep

`-Overwrite` blows away the previous skill subtree wholesale. If you've made local edits inside `<root>/skills/<skill-name>/` or to `<root>/playbooks/INDEX.md`, copy them out first. The clean workflow is to fold those customizations back into the bundle source so they survive the next update — overriding in the install location is a treadmill.

### 4. Apply the update

PowerShell:

```powershell
.\scripts\install.ps1 -Target all -Overwrite
```

Bash:

```bash
OVERWRITE=1 ./scripts/install.sh all
```

Target a narrower scope (`agents`, `claude`, `codex`) if you only want to refresh one install root.

### 5. Prune stale skills (manual)

The installer copies what's in the bundle; it does not delete skills that have been removed upstream. After the update, compare `<root>/skills/` against `<bundle>/skills/` and delete any directories that are no longer in the bundle. Same for `<root>/playbooks/`.

PowerShell snippet:

```powershell
$bundleSkills  = Get-ChildItem "<bundle>\skills" -Directory | Select-Object -ExpandProperty Name
$installed     = Get-ChildItem "$env:USERPROFILE\.claude\skills" -Directory | Select-Object -ExpandProperty Name
$installed | Where-Object { $_ -notin $bundleSkills }
```

Bash snippet:

```bash
diff <(ls <bundle>/skills) <(ls ~/.claude/skills)
```

### 6. Restart the agent

Skills are read at agent startup. Restart Claude Code / Codex / the agent runtime so the refreshed skills load.

### 7. Verify

Spot-check a skill you know changed in this update — open `<root>/skills/<skill-name>/SKILL.md` and confirm the change is present. If you maintain a project-level mirror under `<project>/.claude/skills/` or `<project>/.codex/skills/`, those copies are independent and update separately.

### What the installer does NOT touch

- `<root>/settings.json` — never modified by the installer.
- `<root>/CLAUDE.md`, `<root>/AGENTS.md`, or other personal config at the install root.
- `<root>/projects/` — your conversation/memory state is untouched.
- Anything outside `<root>/skills/` and `<root>/playbooks/`.

### Recovery from a bad update

If an update breaks things, the safe restore path is:

1. `git checkout <previous-tag-or-commit>` in the bundle source (or unzip the previous release).
2. Re-run the installer with `-Overwrite` to roll back the install locations to that version.

There is no built-in version history at the install location — the installer's only state is whatever currently sits in `<root>/skills/` and `<root>/playbooks/`.

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
