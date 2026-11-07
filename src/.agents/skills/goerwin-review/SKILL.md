---
name: goerwin-review
description: Code review, receiving review feedback, review loops, and architecture reviews with saved reports. Use only when explicitly invoked.
argument-hint: "[review request | address feedback | loop … | architecture [folder]]"
disable-model-invocation: true
---

# Goerwin Review

Helpers live in `scripts/` in this skill directory. Run them with `python3` and
an absolute path; they print JSON. Read the repository's instructions,
including AGENTS.local.md, and pass `--github-user USER` if they name a GitHub
account.

## Choose the mode

| The request has | Mode | Read |
|---|---|---|
| Nothing, "review", a PR URL, a branch, or "in isolation with &lt;model&gt;" | Code review | `references/workflows/code-review.md` |
| "address", "receive", "feedback", "reply", "comments", or saved report paths | Receiving | `references/workflows/receiving.md` |
| "loop", or "resume" for a waiting loop | Review loop | `references/workflows/review-loop.md` |
| "architecture", optionally with a folder | Architecture | `references/workflows/architecture.md` |

Ask when a request matches several modes or none. Read only the chosen workflow
and the references it names.

## Confirm before acting

Once the workflow's read-only step has resolved the target, show one summary
and wait for confirmation before editing, writing, or launching anything.
Answer the helper's questions (which PR, which version) first. Include what
applies:

- Mode, repository, and checkout path
- Branch and HEAD SHA; the base or PR and merge-base SHA
- Whether uncommitted changes are included
- Where it runs: this session, a new worktree, or a new Herdr tab
- Model or preset, and rubric
- What gets written (report, sidecars, commits) and what won't happen (push, GitHub posts)
- The helper's warnings

Later gates in a workflow, such as receiving's commit, push, and reply, still
ask separately.

## Reports

Reports go to `~/goerwin-code-reviews/<project>/YYYY-MM-DD-NN-topic.md`
(`--archive` or `GOERWIN_CODE_REVIEWS_DIR` overrides the root) and are
immutable; receiving outcomes go in a `*.receiving.md` sidecar. A PR URL must
belong to the current checkout's repository; never clone. Presets live in
`~/.local/lib/goerwin_tools/presets.json`.

To save a review written in this session, write the body (see
`references/findings.md`) to a temporary file and run, with your own harness,
model, and effort (`unknown` when you can't tell):

~~~sh
python3 /abs/skill/scripts/review.py save --body /tmp/review.md --skill REPORT_ID \
  --harness claude|codex --model MODEL_ID --effort EFFORT \
  [--target-file TARGET.json | --pr URL | --head REF --base REF | --scope PATH] -C /reviewed/checkout
~~~

It prints the saved path; link it in your reply.
