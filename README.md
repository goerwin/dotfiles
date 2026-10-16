# Dotfiles

Personal macOS configuration.

## Install

```sh
make install
source ~/.zshrc
```

To update the configured repositories, then install dotfiles and local apps, run:

```sh
make install-apps
```

First runs `git pull --ff-only` for this repository and each app repository.
Installation starts only after every pull succeeds, with dotfiles installed first.
Shows one-line progress and elapsed time for each update and install, with full
output saved to separate logs in a temporary directory printed at startup.
Stops on the first failure and shows the last 40 lines of its log.

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
