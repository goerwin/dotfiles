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
make lint         # make fix to apply fixes
make build-skills # Preview built skills in build/skills
```

## Skills

Skills live in `src/.agents/skills/`. A `<!-- include: name.md -->` line pulls
in `src/.agents/skills/shared/name.md`, and installing builds each skill into
one self-contained file.

- `$goerwin-babysit`: take work to a ready state, from implementing and
  addressing PR feedback through multi-model review rounds and CI to a draft PR
- `$goerwin-review`: review work by this session or several models, without
  fixing
- `$goerwin-architecture`: review a codebase or folder for design risks
- `$goerwin-mutation`: mutation-test a change's tests
- `$goerwin-handoff`: launch a fresh visible agent

Reports are saved to `~/goerwin-reviews/`. All skills are explicit-only and
ask before pushing or posting to GitHub. Worktrees and agent sessions are left
to the agent orchestrator's own instructions.
