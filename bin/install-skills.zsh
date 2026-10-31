#!/bin/zsh

set -euo pipefail
cd "${0:A:h:h}" || exit 1

skillsInstallHome="${GOERWIN_SKILLS_HOME:-$HOME}"

mkdir -p "$skillsInstallHome/.agents/skills" "$skillsInstallHome/.claude/skills"
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
  mkdir -p "$destination"
  rsync -a --exclude='__pycache__' --exclude='*.pyc' "$source/" "$destination/"
  ln -sfn "../../.agents/skills/$skill" "$claudeLink"
  print -r -- "Installed $skill"
done
mkdir -p "$skillsInstallHome/goerwin-code-reviews"
