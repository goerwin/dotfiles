#!/bin/zsh

set -euo pipefail
cd "${0:A:h:h}" || exit 1

skillsInstallHome="${GOERWIN_SKILLS_HOME:-$HOME}"

sharedDestination="$skillsInstallHome/.agents/shared"
sharedCommands=(goerwin-wts goerwin-review)
if [[ -L "$sharedDestination" ]]; then
  print -u2 -- "Refusing to replace an existing shared helper path."
  exit 1
fi
for command in $sharedCommands; do
  if [[ -e "$skillsInstallHome/.local/bin/$command" && ! -L "$skillsInstallHome/.local/bin/$command" ]]; then
    print -u2 -- "Refusing to replace $skillsInstallHome/.local/bin/$command"
    exit 1
  fi
done
mkdir -p "$sharedDestination" "$skillsInstallHome/.local/bin" \
  "$skillsInstallHome/.agents/skills" "$skillsInstallHome/.claude/skills"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' ./src/.agents/shared/ "$sharedDestination/"
for command in $sharedCommands; do
  ln -sfn "../../.agents/shared/$command" "$skillsInstallHome/.local/bin/$command"
  print -r -- "Installed $command"
done
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
  rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' "$source/" "$destination/"
  ln -sfn "../../.agents/skills/$skill" "$claudeLink"
  print -r -- "Installed $skill"
done
mkdir -p "$skillsInstallHome/goerwin-code-reviews"
