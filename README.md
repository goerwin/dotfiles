# Dotfiles

Personal macOS configuration.

## Install

```sh
zsh install.zsh
source ~/.zshrc
```

## What's included

- Shell configuration
- Supacode worktree commands (`scw` and `supacode-switch`)
- Window management
- Karabiner and key remaps
- VS Code / Cursor settings

## Supacode worktree command

`scw` creates or focuses a worktree for a GitHub pull request. `supacode-switch`
is an alias.

```sh
scw https://github.com/owner/repo/pull/123
```

Requires Python 3.9+, Git, GitHub CLI, and Supacode. See `scw --help` for options.

## Development

```sh
make lint
make fix
```
