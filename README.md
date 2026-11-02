# Dotfiles

Personal macOS dotfiles: shell, Homebrew packages, window management,
key remaps, VS Code / Cursor settings, and agent skills.

## Install

```sh
make install                    # Dotfiles, editor settings, and agent skills
make install-skills             # Agent skills only (see each skill's SKILL.md)
make install-apps APP=mic-muter # Local apps; omit APP for all
```

These `git pull --ff-only` first. Add `NO_UPDATE=1` to install the local
checkout as is, uncommitted changes included (`--no-update` when running a
`bin/` script directly).

## Homebrew

```sh
make brew-backup        # Rewrite src/.Brewfile from installed packages
make install-brew       # Install or upgrade listed packages; keep extras
make install-brew-force # Same, then remove unlisted packages
```

Homebrew must be on your PATH (follow its `brew shellenv` instructions on a new
Mac). Backup drops custom comments and ordering; commit `src/.Brewfile` after
it. It installs as `~/.Brewfile`, so `brew bundle --global` works anywhere.

## Development

```sh
make lint # make fix to apply fixes
make test-skills
```
