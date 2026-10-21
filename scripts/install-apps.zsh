#!/bin/zsh
# alfred-title: Install apps
set -euo pipefail

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

  printf '\n✅ Dotfiles and all apps installed (%s).\n' "$(duration "$((SECONDS - startedAt))")"
}

logDir=$(mktemp -d "${TMPDIR:-/tmp}/install-apps.XXXXXX")
startedAt=$SECONDS
logIdx=0
dotfilesDir="${0:A:h:h}"
previewLines=8
rendererPid=
previewHeader=
currentStep=

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

trap finish EXIT
trap 'stop_preview; print -u2 "✗ Interrupted"; exit 130' INT TERM

# Runs a section of "Name|Success label|command" steps; numbering is derived,
# so adding or removing lines is enough. Commands split with (z), so quote
# paths that contain spaces.
run_section() {
  local title=$1
  shift
  local -a specs=("$@")
  local total=${#specs} i spec name label command started exitCode header
  print
  print -r -- "$title"
  for (( i = 1; i <= total; i++ )); do
    spec="$specs[i]"
    IFS='|' read -r name label command <<<"$spec"
    currentStep=$name
    logIdx=$((logIdx + 1))
    local logFile="$logDir/$(printf '%02d' "$logIdx")-${name//[^a-zA-Z0-9]/-}.log"
    started=$SECONDS
    printf -v header '[%d/%d] %s ... ' "$i" "$total" "$name"
    local -a argv=(${(z)command})
    if run_step "$header" "$logFile" "${argv[@]}"; then
      printf '✓ %s (%s)\n' "$label" "$(duration "$((SECONDS - started))")"
    else
      exitCode=$?
      printf '✗ Failed (exit %d, %s)\n' \
        "$exitCode" "$(duration "$((SECONDS - started))")" >&2
      print -ru2 -- "Last 40 log lines:"
      tail -n 40 "$logFile" >&2
      print -ru2 -- "Full log: $logFile"
      # Exits rather than returns: zsh skips the EXIT trap on errexit.
      exit "$exitCode"
    fi
  done
}

# Runs a step with its output going to logFile. On a terminal, shows a live
# preview of the log below the header and erases it once the step ends, leaving
# the cursor right after the header.
run_step() {
  local header=$1 logFile=$2 exitCode=0
  shift 2
  : >"$logFile"
  if [[ ! -t 1 ]]; then
    print -rn -- "$header"
    "$@" >"$logFile" 2>&1 || exitCode=$?
    return "$exitCode"
  fi
  printf '\e[?25l\e[?7l'
  previewHeader=$header
  draw_preview "$header" "$logFile" &
  rendererPid=$!
  "$@" >"$logFile" 2>&1 || exitCode=$?
  stop_preview
  return "$exitCode"
}

# Redraws the step header with its elapsed time and the last log lines, then
# moves the cursor back to the header row. Autowrap is off while it runs, so
# long lines are clipped instead of wrapping and breaking the line count.
draw_preview() {
  setopt localoptions no_err_exit no_pipe_fail
  local header=$1 logFile=$2 started=$SECONDS frame line
  local -a lines size=(${="$(stty size </dev/tty 2>/dev/null)"})
  local rows=${size[1]:-0} cols=${size[2]:-0} count=$previewLines
  (( cols >= 20 )) || cols=80
  (( rows < 3 )) || (( count = rows - 2 < count ? rows - 2 : count ))
  trap 'exit 0' TERM
  while kill -0 $$ 2>/dev/null; do
    lines=(${(f)"$(tail -n "$count" "$logFile" 2>/dev/null \
      | sed -e $'s/.*\r//' -e $'s/\e\\[[0-9;?]*[A-Za-z]//g')"})
    frame=$'\r\e[J'"$header$(duration "$((SECONDS - started))")"
    for line in "${lines[@]}"; do
      frame+=$'\n\e[2m  │ '"${line[1,cols-6]}"$'\e[0m'
    done
    (( ${#lines} )) && frame+=$'\e['"${#lines}A"
    print -rn -- "$frame"
    sleep 0.25
  done
}

# Stops the running preview (if any), erases it and restores the terminal,
# leaving the cursor right after the step header.
stop_preview() {
  [[ -n "$rendererPid" ]] || return 0
  kill "$rendererPid" 2>/dev/null || true
  wait "$rendererPid" 2>/dev/null || true
  rendererPid=
  printf '\r\e[J\e[?7h\e[?25h%s' "$previewHeader"
}

# Exit trap: on failure or interrupt, ends the output with a summary line.
finish() {
  local exitCode=$? outcome=Failed
  stop_preview
  (( exitCode )) || return 0
  (( exitCode == 130 )) && outcome=Interrupted
  printf '\n❌ %s at %s (%s).\n' "$outcome" "${currentStep:-startup}" \
    "$(duration "$((SECONDS - startedAt))")" >&2
}

duration() {
  printf '%dm %02ds' "$(( $1 / 60 ))" "$(( $1 % 60 ))"
}

# Parse the full sequence before pulling this repository, which may update this file.
main
