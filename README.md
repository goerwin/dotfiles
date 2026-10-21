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
make brew-backup  # Refresh Brewfile after package changes
make brew-restore # Install recorded packages (requires Homebrew)
```

Commit and push `Brewfile` after refreshing. It records package names;
use Time Machine for app data and settings.

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
