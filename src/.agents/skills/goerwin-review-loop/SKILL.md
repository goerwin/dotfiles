---
name: goerwin-review-loop
description: Run headless review → receive → commit rounds on the current local branch until it converges. Use only when explicitly invoked.
argument-hint: "[intent: text, task file paths, images] | resume [answers]"
disable-model-invocation: true
---

# Goerwin Review Loop

The loop is `scripts/review_loop.py` in this skill directory; run it with
`python3` and an absolute path. It prints JSON and blocks until the loop stops.
You only collect choices, start or resume it, and report the result.

## Start

1. Split the user's message into inline intent text, existing file paths
   (task/plan files), and image paths. Don't summarize or rewrite them.
2. Run `python3 ~/.agents/skills/goerwin-code-review/scripts/review_pr.py presets`
   and ask for a **reviewer** and an **implementer** preset in one question
   each. If both use the same model, say a different reviewer catches more and
   ask them to confirm.
3. Confirm once: up to N rounds (default 3) on the current branch against its
   remote default branch; the implementer runs with full permissions; the loop
   commits locally each round and never pushes.

~~~sh
python3 /abs/skill/scripts/review_loop.py start --cwd /checkout \
  --reviewer sol-xhigh --implementer opus-high [--max-rounds 3] [--base origin/main] \
  [--intent "inline text"] [--intent-file TASK.md ...] [--image shot.png ...]
~~~

The worktree must be clean; intent files inside it are exempt and never
committed.

## Results

| Status / stop_reason | Tell the user |
|---|---|
| `no_findings` | Converged. |
| `nothing_applied` | Only pushback remained; list it. |
| `round_limit` | Findings remain after N rounds; list them. |
| `waiting` | Show `questions` and ask for answers. |
| `error` | Show the error; resume after it's fixed. |

Summarize each round from `rounds`: report and sidecar links, applied /
pushed-back / waiting counts, and commits. Nothing was pushed.

## Resume

When the user answers questions (`resume: F2 keep the cursor, …`) or a fixed
error should continue, match answers to the open questions, ask about any left
unanswered, then run:

~~~sh
python3 /abs/skill/scripts/review_loop.py resume --cwd /checkout --answers "F2: keep the cursor; F4: drop it"
~~~

`status --cwd /checkout` lists this checkout's loops and their state files.
