# Code review

Review in place (this session and worktree) unless the user asks for isolation
or names another model to review with.

## In place

~~~sh
python3 /abs/skill/scripts/review.py resolve --in-place ["PR URL"] \
  --cwd "$PWD" [--base REF] [--rubric adversarial] --output /tmp/unique-target.json
~~~

The current branch is compared with its open PR's target branch, or with the
remote default branch when there is no PR (`--base` overrides it); uncommitted
changes are included. Ask first on `pr_selection_required` (which PR) or
`clarification_required`, then show the summary with the helper's `warnings`.

Review by following `references/reviewer.md`, `references/standards.md`, and
the rubric in `references/rubrics/` (`default` unless the user asks for
another). For a PR, read existing comments with `gh pr view URL --comments`.
The diff is `git diff <merge_base_sha>`, so it includes uncommitted work. Write
the report as in `references/findings.md`, save it with
`--skill goerwin-code-review --target-file /tmp/unique-target.json`, and show
the findings with the report link.

## In isolation

Resolve without `--in-place`:

| Status | Ask the user |
|---|---|
| `ready` | Nothing; continue. |
| `revision_selection_required` | GitHub PR version or local committed version; resolve again with `--revision pr\|local`. |
| `pr_selection_required` | Which of the listed PRs. |
| `comparison_confirmation_required` | Confirm the proposed head/base in the summary. |
| `clarification_required` | What PR or head/base they mean. |

Run `review.py presets` and match the named model, or ask for one (never reuse
an earlier choice); it also lists `rubrics`. After the summary is confirmed:

~~~sh
python3 /abs/skill/scripts/review.py launch --target-file /tmp/unique-target.json --preset sol-xhigh
~~~

It creates a review worktree through Worktrunk (setup hooks run first) and
opens the reviewer in a new Herdr tab; only committed changes are reviewed. On
`revision_selection_required`, ask and resolve again. After a launch error or
timeout, check `status --cwd PATH` and Herdr before retrying.
