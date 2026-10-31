# Dotfiles

Personal macOS dotfiles: shell, Homebrew packages, window management,
key remaps, and VS Code / Cursor settings.

## Install

```sh
make install # Install the local checkout, including uncommitted changes
make update # Pull the latest changes (fast-forward only), then install
./bin/install-brew.zsh # Install Homebrew packages
./bin/install-brew-force.zsh # Install Homebrew packages (remove unlisted ones)
make install-apps # Install local apps
make install-apps APP=mic-muter # Update and install only Mic Muter
```

Homebrew must be on your PATH (follow its `brew shellenv` instructions on a new Mac).

## Homebrew

```sh
./bin/brew-backup.zsh        # Refresh package list and generated descriptions
./bin/install-brew.zsh       # Install listed packages; keep extras
./bin/install-brew-force.zsh # Install listed packages; remove unlisted ones
```

The matching `make` targets also work.

Commit and push `src/.Brewfile` after refreshing. It installs as `~/.Brewfile`;
use `brew bundle --global` anywhere. Force install manages Homebrew and uv tools,
keeping required dependencies. Backup replaces custom comments and ordering.
Use Time Machine for app data and settings.

Python versions and CLI tools use `uv` (`uv python install`, `uv tool install`).

## Agent skills

Skills live in `src/.agents/skills` and are included in `make install`.
To install just the skills:

```sh
make install-skills
```

See each skill's `SKILL.md` for usage.

## Development

```sh
make lint
make fix
```
