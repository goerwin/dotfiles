# Personal CLI tools

`goerwin-wt` wraps Worktrunk (`wt`) for worktree operations and coordinates
Herdr spaces and terminals. Start with `goerwin-wt --help` or a subcommand's
`--help`.

Install from the dotfiles checkout with `make install-tools NO_UPDATE=1`.
`make install-skills NO_UPDATE=1` installs the tools and dependent skills.
Commands live in `~/.local/bin`; this reference and the shared Python code
(also used by the `goerwin-review` and `goerwin-handoff` skills) live in
`~/.local/lib/goerwin_tools`.

## Worktrees

```sh
# Create or reuse a checkout, preserving the caller's cwd; stdout is its path.
goerwin-wt switch feat/example origin/main
goerwin-wt switch 123 -C /path/to/repo --json
goerwin-wt switch https://github.com/owner/repo/pull/123 -C /path/to/repo

# Open in Herdr without changing focus, or explicitly focus and raise Herdr.
goerwin-wt switch feat/example --herdr
goerwin-wt switch feat/example --herdr --focus

# Focus an existing checkout without creating an agent or a branch.
goerwin-wt open feat/example
goerwin-wt open /path/to/existing-worktree -C /path/to/repo

# Inspect all registered worktrees in this repository.
goerwin-wt list
goerwin-wt list --json

# Add/reuse a Herdr space for each available checkout; retain current focus.
# Repeating this does not duplicate spaces or launch agents.
goerwin-wt list --herdr
```

`-C` and `--json` work before or after the subcommand. Branch names and
worktree paths select exact targets for `open` and `remove`. `switch` also
accepts PR numbers/URLs; it never clones a missing source repository.
`--github-user USER` selects an existing GitHub login without changing the
globally active account. Existing branches and dirty checkouts are reused
as-is; an optional base applies only to new branches. New branches default
to the fetched remote default. Worktrunk's configured paths and hooks apply.

`switch` never changes its parent shell's directory. A human can use
`cd "$(goerwin-wt switch feat/example)"`; agents can use the JSON `path` as
their working directory. Hook progress goes to stderr.

Plain `list` includes checkout paths and status flags. JSON preserves
Worktrunk's schema-2 envelope (`schema`, `repo`, `collected`, `items`), with
Herdr results added when requested. Missing/prunable checkouts remain listed
but are not opened in Herdr.

Herdr is optional for switching and listing. Explicit UI actions require a
reachable Herdr window and `hc`. Current terminal directories take precedence
over stale space folders when matching existing spaces. UI failures return
nonzero without undoing a successfully created checkout; inspect the output
before retrying. No command changes Herdr's menus, shortcuts, or dialogs.

## Removal

```sh
goerwin-wt remove feat/example -C /path/to/repo
goerwin-wt remove feat/example --stop --json
goerwin-wt remove feat/example --force
goerwin-wt remove feat/example --stop --force
```

The target is required. Main and caller checkouts cannot be removed. Run
from another checkout/session; `-C` alone does not override caller protection.
Locked checkouts remain protected. Detached commits must be retained by a
local branch. Git operations in progress must be completed first.

Removal inspects every matching local Herdr space, live core terminal,
terminal descendants, and discoverable local processes in the checkout.
Duplicate spaces are handled together. A space containing unrelated work or
uninspectable tabs blocks removal before shutdown. A live agent is occupied
even when its reported status is idle. Idle shells without jobs can remain
until space cleanup.

- Without `--stop`, live agents/jobs block removal.
- `--stop` authorizes graceful interruption followed by targeted termination
  and escalation if needed. Shutdown must be verified before deletion.
- `--force` separately authorizes discarding dirty files through Worktrunk;
  it does not authorize stopping processes. Neither flag overrides locks,
  caller protection, or mixed-space checks.

Worktrunk performs removal with `--no-delete-branch --foreground`. Its hooks
and their approvals remain enabled; `--no-hooks` explicitly disables them.
The wrapper does not use `--reap`: that option can leave processes alive and
continue deleting. Process discovery cannot prove the absence of arbitrary
hidden/reparented processes; incomplete known process inspection blocks this
workflow. It never kills by a broad process-name pattern.

After verified deletion, matching Herdr spaces are closed. A reachable Herdr
window is required for safe inspection/cleanup when `herdr-app` is installed.
On systems without Herdr, the same command performs the Worktrunk operation
and local process checks.

Shutdown is irreversible. A hook/removal failure may leave a checkout intact
with agents already stopped; a later UI failure may leave the checkout
removed but its space still present. Nonzero exit and JSON describe the
partial result. Receipts live under the repository's common Git directory at
`goerwin-tools/removals/`. Retry the same target (and `-C` repository) to finish
pending cleanup; recreated paths or unrelated spaces are protected. The
wrapper does not restart stopped agents automatically.

Herdr's native worktree menu retains its upstream behavior. These lifecycle
guarantees apply to this CLI.

## Visible agent handoff

Explicitly invoke `$goerwin-handoff` to transfer work. It uses
`goerwin-wt switch ... --json`, then creates a fresh interactive Codex agent
in a new Herdr tab and focuses it. Existing worktrees/spaces can be reused;
existing agents are never reused, including idle agents. The fresh session
does not depend on the originating agent remaining alive. Resuming a feature
starts with supplied task context rather than restoring an old conversation.

Plain `switch`, `open`, and `list --herdr` never launch agents. General
multi-agent orchestration is outside this workflow.

## Presets

Model presets live in `~/.local/lib/goerwin_tools/presets.json`; the
`goerwin-review` skill lists them with `review.py presets`.
