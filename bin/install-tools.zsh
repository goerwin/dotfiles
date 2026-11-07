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
wtCommand="$toolsBin/goerwin-wt"

managedCommand() { [[ -f "$1" && ! -L "$1" ]] && rg -q '^# goerwin-tools entry point$' "$1" }

if [[ -L "$toolsLibrary" || ( -e "$toolsLibrary" && ! -f "$toolsLibrary/.dotfiles-managed" ) ]]; then
  print -ru2 -- "Refusing to replace an unmanaged tool directory: $toolsLibrary"
  exit 1
fi
if [[ -L "$wtCommand" ]]; then
  print -ru2 -- "Refusing to replace an unrelated command symlink: $wtCommand"
  exit 1
elif [[ -e "$wtCommand" ]] && ! managedCommand "$wtCommand"; then
  print -ru2 -- "Refusing to replace an unmanaged command: $wtCommand"
  exit 1
fi

mkdir -p "$toolsBin" "$toolsLibrary"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' src/.local/lib/goerwin_tools/ "$toolsLibrary/"
install -m 755 src/.local/bin/goerwin-wt "$wtCommand"
print -r -- "Installed goerwin-wt"

# Retired: `goerwin-review save` (now the goerwin-review skill's `review.py save`) and
# ~/.local/share/goerwin-tools (its README now ships in the library).
retired="$toolsBin/goerwin-review"
if managedCommand "$retired"; then
  rm "$retired"
  print -r -- "Removed retired goerwin-review"
elif [[ -e "$retired" || -L "$retired" ]]; then
  print -ru2 -- "Left unrelated goerwin-review untouched: $retired"
fi
retired="$toolsInstallHome/.local/share/goerwin-tools"
if [[ -d "$retired" && ! -L "$retired" && -f "$retired/.dotfiles-managed" ]]; then
  rm -rf "$retired"
  print -r -- "Removed retired $retired"
elif [[ -e "$retired" || -L "$retired" ]]; then
  print -ru2 -- "Left unmanaged $retired untouched"
fi
