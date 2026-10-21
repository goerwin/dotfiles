#!/bin/zsh
# alfred-title: Back up Homebrew packages

set -euo pipefail

cd "${0:A:h:h}" || exit 1

brew bundle dump --file=src/.Brewfile --formula --cask --tap --uv --force
install -m 644 src/.Brewfile "$HOME/.Brewfile"
