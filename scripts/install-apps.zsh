#!/bin/zsh
set -euo pipefail

logDir=$(mktemp -d "${TMPDIR:-/tmp}/install-apps.XXXXXX")
startedAt=$SECONDS
step=0
totalSteps=0
dotfilesDir="${0:A:h:h}"

duration() {
  printf '%dm %02ds' "$(( $1 / 60 ))" "$(( $1 % 60 ))"
}

run_step() {
  local name="$1"
  local logFile="$logDir/$2.log"
  local successLabel="$3"
  shift 3
  local stepStartedAt=$SECONDS
  step=$((step + 1))

  printf '[%d/%d] %s ... ' "$step" "$totalSteps" "$name"
  if "$@" >"$logFile" 2>&1; then
    printf '✓ %s (%s)\n' "$successLabel" "$(duration "$((SECONDS - stepStartedAt))")"
  else
    local exitCode=$?
    printf '✗ Failed (exit %d, %s)\n' \
      "$exitCode" "$(duration "$((SECONDS - stepStartedAt))")" >&2
    print -ru2 -- "Last 40 log lines:"
    tail -n 40 "$logFile" >&2
    print -ru2 -- "Full log: $logFile"
    return "$exitCode"
  fi
}

main() {
  print -r -- "Updating repos and installing dotfiles and apps. Logs: $logDir"
  print
  print -r -- "Updating repositories"
  totalSteps=6
  local repoDir
  for repoDir in "$dotfilesDir" \
    "$HOME/Projects/financer" \
    "$HOME/Projects/noter" \
    "$HOME/Projects/daylier" \
    "$HOME/Projects/mic-muter" \
    "$HOME/Projects/key-remapper"; do
    run_step "${repoDir:t}" "${repoDir:t}-pull" Updated git -C "$repoDir" pull --ff-only
  done

  print
  print -r -- "Installing dotfiles and apps"
  step=0
  totalSteps=7
  run_step "Dotfiles" dotfiles Installed zsh "$dotfilesDir/scripts/install.zsh"
  run_step "Financer (iOS)" financer Installed zsh "$HOME/Projects/financer/ios/install.zsh"
  run_step "Noter (iOS)" noter Installed zsh "$HOME/Projects/noter/install.zsh"
  run_step "Daylier (macOS)" daylier-macos Installed make -C "$HOME/Projects/daylier/ios" install-mac
  run_step "Daylier (iOS)" daylier-ios Installed make -C "$HOME/Projects/daylier/ios" install
  run_step "Mic Muter" mic-muter Installed make -C "$HOME/Projects/mic-muter" install
  run_step "Key Remapper" key-remapper Installed make -C "$HOME/Projects/key-remapper" install

  printf '\nDotfiles and all apps installed (%s).\n' "$(duration "$((SECONDS - startedAt))")"
}

# Parse the full sequence before pulling this repository, which may update this file.
main
