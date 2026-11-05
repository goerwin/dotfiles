---
name: goerwin-handoff
description: When explicitly invoked, create or reuse a Git worktree and hand off context to a fresh interactive Codex agent in a new focused Herdr tab.
---

# Herdr worktree handoff

Invoke this skill only when the user explicitly requests it. Ordinary worktree
creation or opening does not authorize an agent handoff.

Always create a fresh interactive agent in a new tab. Reuse the worktree and
space when appropriate, never an existing agent, including idle sessions.
The new session must remain running when the source agent exits; the launcher
checks that it has no parent dependency.

The outcome is a worktree visible in Herdr's sidebar, a selected agent tab,
and a running interactive Codex session that has received the task context.
An internal subagent or an invisible terminal does not fulfill this skill.

Default to GPT-6.1 Sol with high reasoning for this personal workflow. Honor
an explicitly requested model and effort instead. If the user gives an alias,
resolve it from `~/.local/lib/goerwin_tools/presets.json`; do not silently substitute models.

## Prepare the handoff

Use the branch, PR, or existing worktree the user specified. Reuse an existing
worktree and its uncommitted changes. For a new branch, infer the base from the
task when clear; ask only if choosing the wrong base would change the work.

Write a UTF-8 handoff file outside the repository, preferably in a temporary
task directory. Include the objective, user preferences, scope, relevant links
and paths, investigation findings, changed files, checks already run, unresolved
questions, and the next action. Separate confirmed findings from assumptions.
Exclude credentials. State which external actions are already authorized.

For a continuation handoff, tell the agent to inspect the worktree instructions
and current diff, acknowledge the context, and await the user's next instruction.
For an implementation handoff, give the agent the authorized remaining work.
Do not grant permission to publish, push, or start additional agents merely
because this skill is being used.

## Launch visibly

Use [scripts/launch.py](scripts/launch.py). It accepts a branch, PR number/URL,
or existing worktree directory. Pass `-C` for the source repository and an
optional positional base when creating a branch. An existing branch is reused
as-is; its base is ignored by goerwin-wt switch.

```sh
python3 /path/to/goerwin-handoff/scripts/launch.py fix/example origin/release-2400 \
  -C /path/to/repo --task-file /tmp/task-handoff.md
```

For an existing worktree:

```sh
python3 /path/to/goerwin-handoff/scripts/launch.py /path/to/existing-worktree \
  --task-file /tmp/task-handoff.md --tab-name 'Continue fix · 6.1 Sol High'
```

Use `--model` and `--effort` for explicit overrides. The launcher uses
`goerwin-wt switch TARGET --json` only to resolve/create the checkout without an
extra shell tab. It then explicitly opens the agent tab, selects it, focuses
its pane, and raises Herdr. Never stop after the worktree resolution step.
Codex runs interactively with `--no-daemon`, never `codex exec`, so it stays
watchable and available for follow-up input after the initial turn.

The tools are `goerwin-wt`, `herdr-app`, `hc`, and `codex`. Consult
`herdr-app --skill` or `hc --skill` only if their behavior or schema needs
investigation. Socket errors saying `Operation not permitted` require the
normal sandbox escalation, not another worktree or another agent launch.

## Verify and finish

The launcher prints a receipt path and records the worktree, model, effort,
space, tab, and terminal IDs. It also checks Herdr's selected tab and reports
the terminal's actual program and agent status. If `agent_started` is false
but the terminal is live, inspect that terminal with `hc get` and `hc read`;
use `hc wait TERMINAL --timeout 20` when startup/readiness is pending. A
created tab alone is not proof the agent started or received the handoff.
The handoff is supplied as Codex's initial prompt; confirm its acknowledgment
in the terminal when practical.

If the terminal reports a trust or approval prompt, preserve that decision
for the user. Do not bypass it. Report the blocker and keep the tab visible.
If launch times out or focus fails, inspect the receipt, `herdr-app ls`, and
`hc get` before doing anything else. A timed-out request may have created the
agent; do not rerun the launcher and create a duplicate. Recover by selecting
the recorded tab and focusing its terminal. Never kill unrelated terminals.

Confirm the worktree and tab name, the requested model/effort, and whether
the agent acknowledged the handoff. After a successful continuation handoff,
leave the interactive session running and end the source turn.
