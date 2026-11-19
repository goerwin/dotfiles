# Dotfiles

Personal macOS dotfiles: shell, Homebrew packages, window management,
key remaps, VS Code / Cursor settings, and agent skills.

## Install

```sh
make install                    # Dotfiles, editor settings, and agent skills
make install-skills             # Agent skills
make install-apps APP=mic-muter             # Local apps; omit APP for all
make install-apps APP=financer PLATFORM=ios # ios or mac installs only that platform
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
```

## Reviews and handoffs

Invoke `$goerwin-review` for code review, multi-model council reviews,
addressing feedback, and architecture reviews; reports are saved to
`~/goerwin-reviews/`. Invoke `$goerwin-handoff` to launch a fresh visible agent
in a Herdr tab. Both are explicit-only, use `wt` for worktrees, and ask before
pushing or posting to GitHub.
