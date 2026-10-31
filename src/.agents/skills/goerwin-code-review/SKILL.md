---
name: goerwin-code-review
description: Launch an isolated PR or committed branch review with a freshly selected model and effort. Use only when explicitly invoked.
argument-hint: "[PR URL or review request]"
disable-model-invocation: true
---

# Goerwin Code Review

Stay in the current conversation until the user has chosen a model and effort;
do not fork this launcher into a reviewer. The helper is `scripts/review_pr.py`
in this skill directory. Run it with `python3` and an absolute path; it prints
JSON. Pass custom input as argument arrays or with proper quoting.

## 1. Resolve the target

Read the repository's instructions, including AGENTS.local.md. If they name a
GitHub account, pass `--github-user USER` (it uses that existing `gh` login
without switching the global account).

~~~sh
python3 /abs/skill/scripts/review_pr.py resolve ["PR URL"] \
  --cwd /invoking/checkout --output /tmp/unique-target.json
# or a committed comparison, keeping any review instructions:
python3 /abs/skill/scripts/review_pr.py resolve --cwd /invoking/checkout \
  --head feature/foo --base origin/main --instructions "Focus on pagination" \
  --output /tmp/unique-target.json
~~~

Omit the PR URL to use the current branch. Use a fresh output file for each
invocation. Uncommitted changes are never reviewed and are left untouched.

| Status | Ask the user |
|---|---|
| `ready` | Nothing; continue. |
| `revision_selection_required` | GitHub PR version or local committed version; resolve again with the URL and `--revision pr\|local`. |
| `pr_selection_required` | Which of the listed PRs. |
| `comparison_confirmation_required` | Confirm the proposed head/base (or supply a base if missing). |
| `clarification_required` | What PR or head/base they mean. Never substitute a branch review for a failed PR lookup. |

A PR from an unknown repository needs an existing checkout registered with
`goerwin-wts register /path`. Never clone.

## 2. Require a fresh model and effort choice

Run `review_pr.py presets` and present the presets yourself (the native question
tool if available, otherwise numbered choices). Each option is a model/effort
pair; split into two questions if the UI limits options. Never preselect, reuse
an earlier choice, or launch on timeout. No answer means no worktree and no agent.

## 3. Launch

~~~sh
python3 /abs/skill/scripts/review_pr.py launch \
  --target-file /tmp/unique-target.json --preset sol-xhigh
~~~

The helper rechecks the revisions, prepares an isolated review worktree through
Worktrunk, and opens the reviewer in a new Herdr tab. Parallel reviews of the
same target are fine.

- `revision_selection_required`: ask about the moved revision and resolve again.
- A launch error or timeout: check `status --cwd PATH` and Herdr before retrying;
  a tab may already be running. Focus warnings are not failures.

Report the model/effort, checkout and pending report path. The review finishes
in its own tab; the launcher conversation doesn't receive it.

## Reports

Reports are saved automatically to `~/goerwin-code-reviews/<project>/YYYY-MM-DD-NN-topic.md`
(`--archive` or `GOERWIN_CODE_REVIEWS_DIR` overrides the root), with helper-generated
frontmatter. Finalized reports are immutable; receiving outcomes go in a
`*.receiving.md` sidecar. Use `goerwin-receiving-code-review` to browse and act
on them, `status` to inspect runs, and `launch --dry-run` to see the exact argv.
Edit `presets.json` to change the model list.
