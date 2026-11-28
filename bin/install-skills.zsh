#!/bin/zsh
# alfred-title: Install Skills
# alfred-subtitle: Pull, then install agent skills
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

node lib/build-skills.mjs
mkdir -p "$skillsInstallHome/.agents/skills" "$skillsInstallHome/.claude/skills" "$skillsInstallHome/.codex/skills"
for source in ./build/skills/*(/N); do
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
  if [[ -L "$codexLink" && "${codexLink:A}" != "${destination:A}" ]]; then
    print -u2 -- "Refusing to replace an unrelated Codex skill symlink: $codexLink"
    exit 1
  fi
  mkdir -p "$destination"
  rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' "$source/" "$destination/"
  ln -sfn "../../.agents/skills/$skill" "$claudeLink"
  ln -sfn "../../.agents/skills/$skill" "$codexLink"
  print -r -- "Installed $skill"
done
mkdir -p "$skillsInstallHome/goerwin-reviews"
