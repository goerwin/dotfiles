#!/bin/zsh
# alfred-title: Install tools
# alfred-subtitle: Install personal CLI tools and their shared library

set -euo pipefail
scriptPath=${0:A}
cd "${scriptPath:h:h}" || exit 1
case "${1:-}" in
  --no-update) ;;
  "") git pull --ff-only; exec zsh "$scriptPath" --no-update ;;
  *) print -ru2 -- "Usage: install-tools.zsh [--no-update]"; exit 1 ;;
esac

toolsInstallHome="${GOERWIN_TOOLS_HOME:-$HOME}"
toolsBin="$toolsInstallHome/.local/bin"
toolsLibrary="$toolsInstallHome/.local/lib/goerwin_tools"
toolsDocs="$toolsInstallHome/.local/share/goerwin-tools"
legacyShared="$toolsInstallHome/.agents/shared"
legacyOwned=0
if [[ -L "$toolsBin/goerwin-wts" && "$(readlink "$toolsBin/goerwin-wts")" == ../../.agents/shared/goerwin-wts ]]; then
  legacyOwned=1
fi

managedCommand() { [[ -f "$1" && ! -L "$1" ]] && rg -q '^# goerwin-tools entry point$' "$1" }

for destination in "$toolsLibrary" "$toolsDocs"; do
  if [[ -L "$destination" || ( -e "$destination" && ! -f "$destination/.dotfiles-managed" ) ]]; then
    print -ru2 -- "Refusing to replace an unmanaged tool directory: $destination"
    exit 1
  fi
done
wtCommand="$toolsBin/goerwin-wt"
if [[ -L "$wtCommand" ]]; then
  print -ru2 -- "Refusing to replace an unrelated command symlink: $wtCommand"
  exit 1
elif [[ -e "$wtCommand" ]] && ! managedCommand "$wtCommand"; then
  print -ru2 -- "Refusing to replace an unmanaged command: $wtCommand"
  exit 1
fi

mkdir -p "$toolsBin" "$toolsLibrary" "$toolsDocs"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' src/.local/lib/goerwin_tools/ "$toolsLibrary/"
rsync -a --delete src/.local/share/goerwin-tools/ "$toolsDocs/"
install -m 755 src/.local/bin/goerwin-wt "$wtCommand"
print -r -- "Installed goerwin-wt"
# goerwin-review save is now the goerwin-review skill's `review.py save`.
retired="$toolsBin/goerwin-review"
if managedCommand "$retired" || [[ -L "$retired" && "$(readlink "$retired")" == ../../.agents/shared/goerwin-review ]]; then
  rm "$retired"
  print -r -- "Removed retired goerwin-review"
elif [[ -e "$retired" || -L "$retired" ]]; then
  print -ru2 -- "Left unrelated goerwin-review untouched: $retired"
fi
if (( legacyOwned )); then
  rm "$toolsBin/goerwin-wts"
  if [[ -d "$legacyShared" && ! -L "$legacyShared" ]]; then
    # Older installed skills still import this tree. Back it up only AFTER the
    # skills installer has migrated their helper links and reference paths.
    print -r -- 'goerwin-tools legacy helpers' > "$legacyShared/.goerwin-tools-legacy-owned"
  fi
elif [[ -e "$toolsBin/goerwin-wts" || -L "$toolsBin/goerwin-wts" ]]; then
  print -ru2 -- "Left unrelated goerwin-wts untouched: $toolsBin/goerwin-wts"
fi
