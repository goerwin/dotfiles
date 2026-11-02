#!/bin/zsh
# alfred-title: Install Homebrew packages and remove unlisted ones
# alfred-subtitle: Install or upgrade Brewfile packages, then uninstall unlisted ones

set -euo pipefail

cd "${0:A:h:h}" || exit 1

./bin/install-brew.zsh
brew bundle cleanup --file=src/.Brewfile --formula --cask --tap --uv --force
