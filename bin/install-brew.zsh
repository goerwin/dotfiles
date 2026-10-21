#!/bin/zsh
# alfred-title: Install Homebrew packages

set -euo pipefail

cd "${0:A:h:h}" || exit 1

brew bundle install --file=src/.Brewfile --no-upgrade
install -m 644 src/.Brewfile "$HOME/.Brewfile"
