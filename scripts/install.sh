#!/usr/bin/env bash
set -euo pipefail

target="${1:-all}"
overwrite="${OVERWRITE:-0}"
dry_run="${DRY_RUN:-0}"

case "$target" in
  agents|claude|codex|all) ;;
  *)
    echo "Usage: $0 [agents|claude|codex|all]" >&2
    echo "Set OVERWRITE=1 to replace existing skills/playbooks." >&2
    echo "Set DRY_RUN=1 to preview without copying." >&2
    exit 2
    ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bundle_root="$(cd -- "$script_dir/.." && pwd)"
skills_source="$bundle_root/skills"
playbooks_source="$bundle_root/playbooks"
agents_source="$bundle_root/agents"

# Which agent-definition subfolder a target consumes. The agent-neutral root has no runtime.
agents_subdir_for() {
  case "$1" in
    claude) echo "claude" ;;
    codex)  echo "codex" ;;
    *)      echo "" ;;
  esac
}

copy_dir() {
  local source="$1"
  local destination="$2"

  if [[ -e "$destination" && "$overwrite" != "1" && "$dry_run" == "1" ]]; then
    echo "[dry-run] conflict would block directory $destination"
    return
  fi

  if [[ -e "$destination" && "$overwrite" != "1" ]]; then
    echo "Conflict: $destination already exists. Re-run with OVERWRITE=1 or install a narrower target." >&2
    exit 1
  fi

  if [[ "$dry_run" == "1" ]]; then
    echo "[dry-run] copy directory $source -> $destination"
    return
  fi

  rm -rf -- "$destination"
  cp -R -- "$source" "$destination"
}

copy_file() {
  local source="$1"
  local destination="$2"

  if [[ -e "$destination" && "$overwrite" != "1" && "$dry_run" == "1" ]]; then
    echo "[dry-run] conflict would block file $destination"
    return
  fi

  if [[ -e "$destination" && "$overwrite" != "1" ]]; then
    echo "Conflict: $destination already exists. Re-run with OVERWRITE=1 or merge manually." >&2
    exit 1
  fi

  if [[ "$dry_run" == "1" ]]; then
    echo "[dry-run] copy file $source -> $destination"
    return
  fi

  cp -- "$source" "$destination"
}

targets=()
if [[ "$target" == "all" ]]; then
  targets=(agents claude codex)
else
  targets=("$target")
fi

if [[ "$overwrite" != "1" && "$dry_run" != "1" ]]; then
  conflicts=()
  for name in "${targets[@]}"; do
    root="$HOME/.$name"
    skills_dest="$root/skills"
    playbooks_dest="$root/playbooks"

    for skill in "$skills_source"/*; do
      [[ -d "$skill" ]] || continue
      destination="$skills_dest/$(basename "$skill")"
      [[ ! -e "$destination" ]] || conflicts+=("$destination")
    done

    for playbook in "$playbooks_source"/*; do
      [[ -f "$playbook" ]] || continue
      destination="$playbooks_dest/$(basename "$playbook")"
      [[ ! -e "$destination" ]] || conflicts+=("$destination")
    done

    sub="$(agents_subdir_for "$name")"
    if [[ -n "$sub" && -d "$agents_source/$sub" ]]; then
      for agent in "$agents_source/$sub"/*; do
        [[ -f "$agent" ]] || continue
        destination="$root/agents/$(basename "$agent")"
        [[ ! -e "$destination" ]] || conflicts+=("$destination")
      done
    fi
  done

  if (( ${#conflicts[@]} > 0 )); then
    echo "Install blocked by existing files. Re-run with OVERWRITE=1 or install a narrower target:" >&2
    printf '  %s\n' "${conflicts[@]}" >&2
    exit 1
  fi
fi

for name in "${targets[@]}"; do
  root="$HOME/.$name"
  skills_dest="$root/skills"
  playbooks_dest="$root/playbooks"

  if [[ "$dry_run" == "1" ]]; then
    echo "[dry-run] ensure $skills_dest"
    echo "[dry-run] ensure $playbooks_dest"
  else
    mkdir -p -- "$skills_dest" "$playbooks_dest"
  fi

  for skill in "$skills_source"/*; do
    [[ -d "$skill" ]] || continue
    copy_dir "$skill" "$skills_dest/$(basename "$skill")"
  done

  for playbook in "$playbooks_source"/*; do
    [[ -f "$playbook" ]] || continue
    copy_file "$playbook" "$playbooks_dest/$(basename "$playbook")"
  done

  sub="$(agents_subdir_for "$name")"
  if [[ -n "$sub" && -d "$agents_source/$sub" ]]; then
    agents_dest="$root/agents"
    if [[ "$dry_run" == "1" ]]; then
      echo "[dry-run] ensure $agents_dest"
    else
      mkdir -p -- "$agents_dest"
    fi
    for agent in "$agents_source/$sub"/*; do
      [[ -f "$agent" ]] || continue
      copy_file "$agent" "$agents_dest/$(basename "$agent")"
    done
    echo "  agents: $agents_dest"
  fi

  echo "Installed target: $name"
  echo "  skills: $skills_dest"
  echo "  playbooks: $playbooks_dest"
done

echo "Installed skills:"
for skill in "$skills_source"/*; do
  [[ -d "$skill" ]] || continue
  echo "  /$(basename "$skill")"
done

cat <<'EOF'

Config snippets (not written) - add by hand so unnamed subagents also land on the cheap tier:

  Claude Code  ~/.claude/settings.json
    "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet" }

  Codex        ~/.codex/config.toml
    [agents]
    default_subagent_model = "gpt-6-luna"
    default_subagent_reasoning_effort = "low"
EOF
