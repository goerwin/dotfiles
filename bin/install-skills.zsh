#!/bin/zsh
# alfred-title: Install skills
# alfred-subtitle: Pull, then install agent skills and supporting CLI tools
# alfred-args: --no-update: skip git pull and install the local skills as is

set -euo pipefail
scriptPath=${0:A}
cd "${scriptPath:h:h}" || exit 1

# Pulls, then reruns the updated installer with --no-update.
case "${1:-}" in
  --no-update) ;;
  "")
    print -r -- "Pulling latest dotfiles"
    git pull --ff-only
    exec zsh "$scriptPath" --no-update ;;
  *) print -ru2 -- "Usage: install-skills.zsh [--no-update]"; exit 1 ;;
esac

skillsInstallHome="${GOERWIN_SKILLS_HOME:-$HOME}"

GOERWIN_TOOLS_HOME="$skillsInstallHome" zsh bin/install-tools.zsh --no-update
mkdir -p "$skillsInstallHome/.agents/skills" "$skillsInstallHome/.claude/skills" "$skillsInstallHome/.codex/skills"
for source in ./src/.agents/skills/*(/N); do
  [[ -f "$source/SKILL.md" ]] || continue
  skill="${source:t}"
  destination="$skillsInstallHome/.agents/skills/$skill"
  if [[ -L "$destination" ]]; then
    print -u2 -- "Refusing to replace the installed skill symlink: $destination"
    exit 1
  fi
  claudeLink="$skillsInstallHome/.claude/skills/$skill"
  if [[ -e "$claudeLink" && ! -L "$claudeLink" ]]; then
    print -u2 -- "Refusing to replace a Claude skill directory: $claudeLink"
    exit 1
  fi
  codexLink="$skillsInstallHome/.codex/skills/$skill"
  if [[ -e "$codexLink" && ! -L "$codexLink" ]]; then
    print -u2 -- "Refusing to replace a Codex skill directory: $codexLink"
    exit 1
  fi
  if [[ -L "$codexLink" && "${codexLink:A}" != "${source:A}" && "${codexLink:A}" != "${destination:A}" ]]; then
    print -u2 -- "Refusing to replace an unrelated Codex skill symlink: $codexLink"
    exit 1
  fi
  mkdir -p "$destination"
  rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' "$source/" "$destination/"
  ln -sfn "../../.agents/skills/$skill" "$claudeLink"
  # Preserve an existing direct link to this checkout, including in-progress skills.
  if [[ ! -L "$codexLink" || "${codexLink:A}" != "${source:A}" ]]; then
    ln -sfn "../../.agents/skills/$skill" "$codexLink"
  fi
  print -r -- "Installed $skill"
done
# These skills are now modes of goerwin-review. Retire only the installer's own copies and links.
retiredBackup=
for skill in goerwin-code-review goerwin-receiving-code-review goerwin-review-loop goerwin-architecture-review; do
  installed="$skillsInstallHome/.agents/skills/$skill"
  if [[ -d "$installed" && ! -L "$installed" ]] && rg -q "^name: $skill\$" "$installed/SKILL.md" 2>/dev/null; then
    mkdir -p "$skillsInstallHome/.local/state/goerwin-tools"
    : ${retiredBackup:=$(mktemp -d "$skillsInstallHome/.local/state/goerwin-tools/retired-skills.XXXXXX")}
    mv "$installed" "$retiredBackup/$skill"
    print -r -- "Retired $skill into $retiredBackup (now part of goerwin-review)"
  elif [[ -e "$installed" || -L "$installed" ]]; then
    print -u2 -- "Left $installed untouched; it isn't an installed copy of $skill"
  fi
  for link in "$skillsInstallHome/.claude/skills/$skill" "$skillsInstallHome/.codex/skills/$skill"; do
    [[ -e "$link" || -L "$link" ]] || continue
    target=$(readlink "$link" || true)
    if [[ ! -e "$installed" && ( "$target" == "../../.agents/skills/$skill" || "$target" == "${PWD:A}/src/.agents/skills/$skill" ) ]]; then
      rm "$link"
    else
      print -u2 -- "Left $link untouched; remove it if it's an old copy of $skill"
    fi
  done
done
legacyShared="$skillsInstallHome/.agents/shared"
if [[ -d "$legacyShared" && ! -L "$legacyShared" && -f "$legacyShared/.goerwin-tools-legacy-owned" ]]; then
  mkdir -p "$skillsInstallHome/.local/state/goerwin-tools"
  legacyBackup=$(mktemp -d "$skillsInstallHome/.local/state/goerwin-tools/legacy-shared.XXXXXX")
  mv "$legacyShared" "$legacyBackup/shared"
  print -r -- "Preserved legacy helpers in $legacyBackup/shared"
fi
mkdir -p "$skillsInstallHome/goerwin-code-reviews"
