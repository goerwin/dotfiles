#!/bin/zsh
# alfred-title: Install Homebrew packages
# alfred-subtitle: Install or upgrade Brewfile packages · keeps unlisted ones

set -euo pipefail

cd "${0:A:h:h}" || exit 1

brew bundle install --file=src/.Brewfile --upgrade
install -m 644 src/.Brewfile "$HOME/.Brewfile"
