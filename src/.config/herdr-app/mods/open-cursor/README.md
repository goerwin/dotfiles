# Open the selected space in Cursor

A Herdr App mod for macOS that opens the selected space/worktree's saved
folder in Cursor. Requires Cursor to be installed and the folder to be
available on this Mac.

## Install

1. Copy this directory to `mods/open-cursor/` inside your Herdr App home:
   `~/.config/herdr-app` by default, or the directory set by `$HERDR_APP_HOME`.
2. In that home's `keys.json`, bind `mod.open:open-cursor` to a shortcut of
   your choice in the `global` section. Preserve your existing bindings.

You can also invoke it without a key binding:

```sh
herdr-app do mod.open --name open-cursor
```

## Behavior

The target is the selected space's saved folder. Changing directory in a
terminal does not change the target, and Git is not involved.

The mod loads on demand in a transparent window that preserves terminal
focus and closes after the launch finishes. Failures appear as a notification.

## Validate

Run `herdr-app check` with the installed mod directory as its argument.
This loads and renders the mod without launching Cursor.
