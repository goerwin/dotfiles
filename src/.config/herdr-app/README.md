# Herdr app

Personal shortcuts that use Herdr's native layout, tab bar, and Agents panel.

<!-- TODO: Revisit these workarounds as upstream improves tab reordering and mod extensibility.
- Tab drag feedback: https://github.com/herdrdev/herdr-app/issues/382
- Cloned-mod maintenance: https://github.com/herdrdev/herdr-app/issues/289
- Native tab-bar extension support: https://github.com/herdrdev/herdr-app/pull/247
-->

## Tab shortcuts

- **Cmd+,** moves the active tab one position left.
- **Cmd+.** moves it one position right.
- Moving stops at either end and keeps the same tab focused.

The two small, invisible action mods call Herdr's native `tab.move` command
and close immediately. Both use the implementation in
`mods/move-tab-left/main.js` (the right mod links to it). Install both folders
together and preserve the symlink. The shortcuts work with Herdr's native layout.

Cmd+, replaces the Settings shortcut. Settings is available in the sidebar
and command palette.

## Install

From the dotfiles repo, run `make install` (or `make install NO_UPDATE=1` to
use the local checkout). For a custom `$HERDR_APP_HOME`, copy this directory's
contents there instead.

Use Herdr's native layout:

```sh
herdr-app do layout.switch --name main
```

In the Agents sidebar, open the sort menu next to **Agents** and choose
**Grouped by space**. This replaces status headings (Idle, Done, Working,
Needs you) with space names and groups agents by space instead of priority.
Herdr remembers the layout and grouping; runtime state is not tracked here.

The existing `confirm-close` and `open-cursor` mods remain separate shortcuts.

## GoDaddy AI usage

The `main-godaddy-ai` layout shows one status bar mod with the current spend and
budget for Gocode and Cursor, for example `Gocode $366.49/$800 - Cursor $201/$500`.
GoCode shows the key's spend and `max_budget` when the key has a budget.
Otherwise it reads the key owner's spend and budget. Cursor uses the
individual team usage limit. The mod uses the existing local
`GOCODE_API_KEY` and `GOCODE_BASE_URL`.

Set up Cursor in your local `~/.zshenv` using the usage dashboard in Chrome:

```zsh
# CURSOR_TEAM_ID: copy teamId from the usage-summary request in DevTools > Network.
export CURSOR_TEAM_ID='…'
# CURSOR_SESSION: copy WorkosCursorSessionToken from DevTools > Application > Cookies > cursor.com.
export CURSOR_SESSION='…'
```

Keep the session cookie in your local shell configuration. After installing
the dotfiles, select the layout to show the usage bar:

```sh
herdr-app do layout.switch --name main-godaddy-ai
```

## Validate

After installation:

```sh
herdr-app check ~/.config/herdr-app/mods/move-tab-left
herdr-app check ~/.config/herdr-app/mods/move-tab-right
herdr-app check ~/.config/herdr-app/mods/godaddy-ai
herdr-app status
```
