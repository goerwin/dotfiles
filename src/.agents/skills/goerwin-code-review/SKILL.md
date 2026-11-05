---
name: goerwin-code-review
description: Review the current branch in place (or a PR/branch comparison in an isolated worktree) and save the report. Use only when explicitly invoked.
argument-hint: "[PR URL, review request, or 'in isolation with <model>']"
disable-model-invocation: true
---

# Goerwin Code Review

The helper is `scripts/review_pr.py` in this skill directory. Run it with
`python3` and an absolute path; it prints JSON. Read the repository's
instructions, including AGENTS.local.md, and pass `--github-user USER` if they
name a GitHub account.

Review **in place** (this session, this worktree) unless the user asks for an
isolated review or names a different model to review with.

## In place (default)

~~~sh
python3 /abs/skill/scripts/review_pr.py resolve --in-place ["PR URL"] \
  --cwd "$PWD" [--base REF] [--rubric adversarial] --output /tmp/unique-target.json
~~~

The current branch is reviewed against its open PR's target branch, or against
the remote default branch when there is no PR (`--base` overrides it).
Uncommitted changes are included. Show any `warnings` (out of sync with the PR,
uncommitted changes) and ask the user to confirm before reviewing. Other
statuses need a question first: `pr_selection_required` (which PR) or
`clarification_required`.

Then review yourself, following `references/reviewer.md` and the rubric in
`references/rubrics/` (`default` unless the user asks for another). The diff is
`git diff <merge_base_sha>` in this worktree, so it includes uncommitted work.
Don't edit files while reviewing. Write the body to a temporary file and save:

~~~sh
goerwin-review save --target-file /tmp/unique-target.json --body /tmp/review.md \
  --skill goerwin-code-review --harness claude|codex --model YOUR_MODEL_ID --effort YOUR_EFFORT|unknown
~~~

Use your own model ID; use `unknown` for effort if you can't tell. Show the
findings and link the saved report.

## In isolation

When the user asks for isolation or another model ("review in isolation with
Sol xhigh"), resolve without `--in-place`:

| Status | Ask the user |
|---|---|
| `ready` | Nothing; continue. |
| `revision_selection_required` | GitHub PR version or local committed version; resolve again with `--revision pr\|local`. |
| `pr_selection_required` | Which of the listed PRs. |
| `comparison_confirmation_required` | Confirm the proposed head/base. |
| `clarification_required` | What PR or head/base they mean. |

Run `review_pr.py presets` and match the named model, or ask for one (never
reuse an earlier choice). The same output lists `rubrics`. Then:

~~~sh
python3 /abs/skill/scripts/review_pr.py launch --target-file /tmp/unique-target.json --preset sol-xhigh
~~~

It creates a review worktree through Worktrunk (setup hooks run first) and opens
the reviewer in a new Herdr tab. Only committed changes are reviewed. On
`revision_selection_required`, ask and resolve again. After a launch error or
timeout, check `status --cwd PATH` and Herdr before retrying.

## Reports

Reports go to `~/goerwin-code-reviews/<project>/YYYY-MM-DD-NN-topic.md`
(`--archive` or `GOERWIN_CODE_REVIEWS_DIR` overrides the root) and are
immutable; receiving outcomes go in a `*.receiving.md` sidecar. Use
`goerwin-receiving-code-review` to act on them. A PR URL must belong to the
current checkout's repository; never clone.
Presets live in `~/.local/lib/goerwin_tools/presets.json`.
