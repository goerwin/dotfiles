# Review loop

Headless review → receive → commit rounds on the current local branch until it
converges. The loop is `scripts/review_loop.py`; it blocks until the loop
stops. You only collect choices, start or resume it, and report the result.

## Start

1. Take loop settings out of the user's message: round count ("5 rounds" →
   `--max-rounds 5`), base ("against develop" → `--base`), reviewer and
   implementer models when named ("review with Sol xhigh"), and the reviewer
   rubric ("adversarial" → `--rubric adversarial`; otherwise `default`). Split
   the rest into inline intent text, existing file paths (task/plan files), and
   image paths, without summarizing or rewriting them. Settings never go into
   the intent.
2. Run `review.py presets`. Match named models to presets; ask only for a role
   that is unnamed or ambiguous. If both roles use the same model, say a
   different reviewer catches more and ask them to confirm.
3. Show the summary: rounds (default 3), base (default the remote default
   branch), both presets, rubric, and the intent sources. Reviewers get fresh
   worktrees (setup hooks run first); the implementer works here with full
   permissions; the result is one local commit and nothing is pushed.

~~~sh
python3 /abs/skill/scripts/review_loop.py start --cwd /checkout \
  --reviewer sol-xhigh --implementer opus-high [--rubric adversarial] [--max-rounds 3] [--base origin/main] \
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

When `status` is `squash_pending`, the loop finished with round commits. Read
`git diff <start_head>`, write one short conventional subject for what changed
(e.g. `fix: keep cursors stable across pages`), and fold the rounds into one
commit:

~~~sh
python3 /abs/skill/scripts/review_loop.py squash --cwd /checkout --message "fix: …"
~~~

Only the loop's commits are folded; the body lists each round's report. Then
summarize each round from `rounds`: report and sidecar links, applied /
pushed-back / waiting counts, and the final commit. Nothing was pushed.

## Resume

When the user answers questions (`resume: F2 keep the cursor, …`) or a fixed
error should continue, match answers to the open questions, ask about any left
unanswered, then run:

~~~sh
python3 /abs/skill/scripts/review_loop.py resume --cwd /checkout --answers "F2: keep the cursor; F4: drop it"
~~~

`status --cwd /checkout` lists this checkout's loops and their state files.
