#!/bin/zsh
set -euo pipefail

logDir=$(mktemp -d "${TMPDIR:-/tmp}/install-apps.XXXXXX")
startedAt=$SECONDS
step=0

duration() {
  printf '%dm %02ds' "$(( $1 / 60 ))" "$(( $1 % 60 ))"
}

run_install() {
  local name="$1"
  local logFile="$logDir/$2.log"
  shift 2
  local stepStartedAt=$SECONDS
  step=$((step + 1))

  printf '[%d/6] %s ... ' "$step" "$name"
  if "$@" >"$logFile" 2>&1; then
    printf '✓ Installed (%s)\n' "$(duration "$((SECONDS - stepStartedAt))")"
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

print -r -- "Installing local apps. Logs: $logDir"
print

run_install "Financer (iOS)" financer zsh "$HOME/Projects/financer/ios/install.zsh"
run_install "Noter (iOS)" noter zsh "$HOME/Projects/noter/install.zsh"
run_install "Daylier (macOS)" daylier-macos make -C "$HOME/Projects/daylier/ios" install-mac
run_install "Daylier (iOS)" daylier-ios make -C "$HOME/Projects/daylier/ios" install
run_install "Mic Muter" mic-muter make -C "$HOME/Projects/mic-muter" install
run_install "Key Remapper" key-remapper make -C "$HOME/Projects/key-remapper" install

printf '\nAll apps installed (%s).\n' "$(duration "$((SECONDS - startedAt))")"
