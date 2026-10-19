#!/bin/zsh
set -euo pipefail

logDir=$(mktemp -d "${TMPDIR:-/tmp}/install-apps.XXXXXX")
startedAt=$SECONDS
logIdx=0
dotfilesDir="${0:A:h:h}"

# iPhone UDID for the repo's iOS install scripts, which require it in the
# environment. Taken from the environment or this repo's gitignored .env.
IOS_DEVICE_UDID="${IOS_DEVICE_UDID:-}"
if [[ -z "$IOS_DEVICE_UDID" && -r "$dotfilesDir/.env" ]]; then
  IOS_DEVICE_UDID="$(source "$dotfilesDir/.env" && print -r -- "${IOS_DEVICE_UDID:-}")"
fi
if [[ -z "$IOS_DEVICE_UDID" ]]; then
  print -ru2 -- "IOS_DEVICE_UDID is not set."
  print -ru2 -- "Add it to $dotfilesDir/.env as IOS_DEVICE_UDID=\"<device-udid>\" (or export it)."
  exit 1
fi
export IOS_DEVICE_UDID

source "$dotfilesDir/scripts/install-ios-lib.zsh"

duration() {
  printf '%dm %02ds' "$(( $1 / 60 ))" "$(( $1 % 60 ))"
}

# Runs a section of "Name|Success label|command" steps; numbering is derived,
# so adding or removing lines is enough. Commands split with (z), so quote
# paths that contain spaces.
run_section() {
  local title=$1
  shift
  local -a specs=("$@")
  local total=${#specs} i spec name label command started exitCode
  print
  print -r -- "$title"
  for (( i = 1; i <= total; i++ )); do
    spec="$specs[i]"
    IFS='|' read -r name label command <<<"$spec"
    logIdx=$((logIdx + 1))
    local logFile="$logDir/$(printf '%02d' "$logIdx")-${name//[^a-zA-Z0-9]/-}.log"
    started=$SECONDS
    printf '[%d/%d] %s ... ' "$i" "$total" "$name"
    local -a argv=(${(z)command})
    if "${argv[@]}" >"$logFile" 2>&1; then
      printf '✓ %s (%s)\n' "$label" "$(duration "$((SECONDS - started))")"
    else
      exitCode=$?
      printf '✗ Failed (exit %d, %s)\n' \
        "$exitCode" "$(duration "$((SECONDS - started))")" >&2
      print -ru2 -- "Last 40 log lines:"
      tail -n 40 "$logFile" >&2
      print -ru2 -- "Full log: $logFile"
      return "$exitCode"
    fi
  done
}

main() {
  print -r -- "Updating repos and installing dotfiles and apps. Logs: $logDir"

  run_section "Preflight checks" \
    "iPhone reachable|Checked|ios_check_device" \
    "Signing credentials|Checked|ios_check_signing"

  run_section "Updating repositories" \
    "dotfiles|Updated|git -C $dotfilesDir pull --ff-only" \
    "financer|Updated|git -C $HOME/Projects/financer pull --ff-only" \
    "noter|Updated|git -C $HOME/Projects/noter pull --ff-only" \
    "daylier|Updated|git -C $HOME/Projects/daylier pull --ff-only" \
    "mic-muter|Updated|git -C $HOME/Projects/mic-muter pull --ff-only" \
    "key-remapper|Updated|git -C $HOME/Projects/key-remapper pull --ff-only"

  run_section "Installing dotfiles and apps" \
    "Dotfiles|Installed|zsh $dotfilesDir/scripts/install.zsh" \
    "Financer (iOS)|Installed|zsh $HOME/Projects/financer/ios/install.zsh" \
    "Noter (iOS)|Installed|zsh $HOME/Projects/noter/install.zsh" \
    "Daylier (macOS)|Installed|make -C $HOME/Projects/daylier/ios install-mac" \
    "Daylier (iOS)|Installed|make -C $HOME/Projects/daylier/ios install" \
    "Mic Muter|Installed|make -C $HOME/Projects/mic-muter install" \
    "Key Remapper|Installed|make -C $HOME/Projects/key-remapper install"

  printf '\nDotfiles and all apps installed (%s).\n' "$(duration "$((SECONDS - startedAt))")"
}

# Parse the full sequence before pulling this repository, which may update this file.
main
