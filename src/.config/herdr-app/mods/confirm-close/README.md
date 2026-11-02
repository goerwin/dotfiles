# Confirm tab close

A Herdr App mod that confirms before closing tabs with running work.
Idle shells close silently after an invisible process check.

## Install

1. Copy this folder to `mods/confirm-close/` under `~/.config/herdr-app`
   (or `$HERDR_APP_HOME`).
2. In `keys.json`, bind your preferred shortcut to `mod.open:confirm-close`
   under `global`.

Only this action is protected; Herdr's close buttons remain unchanged.

## Behavior

- Agents, foreground programs, background jobs, and unavailable process
  information trigger confirmation. Persistent shell helpers may also prompt.
- Enter confirms; Escape or Cancel keeps the tab running.
- Switching tabs during inspection does not change the target.
- Herdr's last-tab / space confirmation still applies.

Process checks are snapshots; jobs can start or finish afterward.

## Validate

From this folder (neither check closes real tabs):

```sh
herdr-app check .
node --experimental-vm-modules --test tests/confirm-close.test.mjs
```
