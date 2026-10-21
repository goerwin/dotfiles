# Dotfiles

Personal macOS dotfiles: shell, Homebrew packages, window management,
key remaps, and VS Code / Cursor settings.

## Install

```sh
make install
source ~/.zshrc
make install-apps # Update repos and install dotfiles + local apps
```

## Homebrew

```sh
make brew-backup        # Refresh package list and generated descriptions
make install-brew       # Install listed packages; keep extras
make install-brew-force # Install listed packages; remove unlisted ones
```

Commit and push `src/.Brewfile` after refreshing. It installs as `~/.Brewfile`;
use `brew bundle --global` anywhere. Force install manages Homebrew and uv tools,
keeping required dependencies. Backup replaces custom comments and ordering.
Use Time Machine for app data and settings.

Python versions and CLI tools use `uv` (`uv python install`, `uv tool install`).

## Supacode worktrees

Create or focus a PR worktree (`supacode-switch` is an alias):

```sh
scs https://github.com/owner/repo/pull/123
```

Requires Python 3.9+, Git, GitHub CLI, and Supacode. See `scs --help`.

## Development

```sh
make lint
make fix
```
