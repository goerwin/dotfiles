---
name: goerwin-handoff
description: When explicitly invoked, hand off the current task to a fresh interactive agent in a new Herdr tab, in a new or existing Worktrunk worktree.
disable-model-invocation: true
---

# Herdr handoff

Use only when the user explicitly asks. The outcome is a visible tab in the
Herdr app running a fresh interactive agent that received the handoff and keeps
running after this session ends. An internal subagent, `codex exec`, or
`claude -p` doesn't count. Never reuse an existing agent.

## Prepare

- **Checkout:** use the branch, PR, or worktree the user named, keeping its
  uncommitted changes. Create a new worktree only when the work needs another
  branch or must run alongside further edits here; otherwise use this checkout
  and stop editing it. Infer the base from the task; ask only if the wrong base
  would change the work.
- **Agent:** Codex with the latest frontier GPT Sol model at high effort,
  unless the user names another model or Claude.
- **Handoff file:** write it outside the repository (e.g.
  `/tmp/handoff-NAME.md`): objective, user preferences, scope, links and
  paths, findings (confirmed versus assumed), changed files, checks already
  run, open questions, the next action, and which actions are authorized. No
  credentials. For a continuation, tell the agent to inspect the current diff,
  acknowledge, and wait for the user. Never grant push, publish, or starting
  more agents just because of the handoff.

## Confirm

Show the repository, branch or worktree (new or reused, with the base for a new
branch), the agent's exact model and effort, the tab name, a few lines on the
objective and next action, and what the agent may do. Wait for confirmation.

## Launch

Create worktrees only with `wt`, never `git worktree add`. Then open the agent
in a tab of the Herdr space for that folder (find it in `herdr-app ls`), or in
a new space if there is none. Unsetting `HC_TERMINAL_ID` keeps the agent from
ending with this session.

```sh
wt switch --create BRANCH --base BASE --no-cd --format json   # existing branch: drop --create/--base
env -u HC_TERMINAL_ID herdr-app do tab.new --space SPACE --name "TAB" --folder PATH \
  --argv '["codex","--no-daemon","--model","MODEL","-c","model_reasoning_effort=\"high\""]' \
  --task "Read /tmp/handoff-NAME.md and follow it."
# no space yet: herdr-app do space.new --name BRANCH --folder PATH --tab "TAB" --argv … --task …
```

For Claude, also unset `CLAUDECODE` and `CLAUDE_CODE_EFFORT_LEVEL`, and use
`--argv '["claude","--model","MODEL","--effort","high"]'`.

The reply holds the new `terminal` ID. Confirm the agent with `hc get TERMINAL`
(live, the right program and folder, no parent), `hc wait TERMINAL --timeout 20`
while it starts, and `hc read TERMINAL` for its acknowledgment. If it shows a
trust or approval prompt, leave it for the user and say so. A timeout doesn't
prove failure: check `herdr-app ls` and `hc get` before doing anything else,
and never launch a duplicate. Never kill unrelated terminals.

Report the worktree, tab, model and effort, and whether the agent acknowledged
the handoff. After a continuation handoff, end your turn.

## Removing a worktree

Only when the user asks. If `hc ls` shows an agent still running in it, stop
and ask. Otherwise close its space (`herdr-app do space.close --id SPACE
--confirmed true`), then run `wt remove BRANCH` from another checkout.
