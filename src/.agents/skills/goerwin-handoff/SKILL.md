---
name: goerwin-handoff
description: When explicitly invoked, hand off the current task to a fresh, visible interactive agent that keeps running after this session ends.
disable-model-invocation: true
---

# Goerwin handoff

Use only when the user explicitly asks. The outcome is a fresh interactive
agent, visible to the user, that received the handoff and keeps running after
this session ends. An internal subagent or a one-shot, non-interactive run
doesn't count. Never reuse an existing agent.

## Prepare

- **Checkout:** use the branch or PR the user named, keeping its uncommitted
  changes. Use a separate checkout only when the work needs another branch or
  must run alongside further edits here; otherwise use this checkout and stop
  editing it. Infer the base from the task; ask only if the wrong base would
  change the work.
- **Agent:** the agent and model the user names; otherwise the same agent as
  this session with its latest frontier model at high effort.
- **Handoff file:** write it outside the repository (e.g.
  `/tmp/handoff-NAME.md`): objective, user preferences, scope, links and
  paths, findings (confirmed versus assumed), changed files, checks already
  run, open questions, the next action, and which actions are authorized. No
  credentials. For a continuation, tell the agent to inspect the current diff,
  acknowledge, and wait for the user. Never grant push, publish, or starting
  more agents just because of the handoff.

## Confirm

Show the repository, branch (new or existing, with the base for a new one),
the agent's exact model and effort, a few lines on the objective and next
action, and what the agent may do. Wait for confirmation.

## Launch

Create the checkout and start the agent the way your agent orchestrator
documents, with the prompt "Read /tmp/handoff-NAME.md and follow it."

Confirm the agent is running the right program in the right folder and read
its acknowledgment. If it shows a trust or approval prompt, leave it for the
user and say so. A timeout doesn't prove failure: check whether the agent
started before doing anything else, and never launch a duplicate.

Report the checkout, model and effort, where the agent runs, and whether it
acknowledged the handoff. After a continuation handoff, end your turn.
