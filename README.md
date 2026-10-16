# Dotfiles

Personal macOS configuration.

## Install

```sh
make install
source ~/.zshrc
```

To install Financer, Noter, Daylier (macOS and iOS), Mic Muter, and Key Remapper
from their repositories in `~/Projects`, run:

```sh
make install-apps
```

Shows progress and elapsed time for each install, with full output saved to
separate logs in a temporary directory printed at startup. Stops on the first
failure and shows the last 40 lines of its log.

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
