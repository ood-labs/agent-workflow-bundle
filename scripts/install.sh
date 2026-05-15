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

  echo "Installed target: $name"
  echo "  skills: $skills_dest"
  echo "  playbooks: $playbooks_dest"
done

echo "Installed skills:"
for skill in "$skills_source"/*; do
  [[ -d "$skill" ]] || continue
  echo "  /$(basename "$skill")"
done
