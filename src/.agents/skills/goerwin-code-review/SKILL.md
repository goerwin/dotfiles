---
name: goerwin-code-review
description: Launch an isolated PR or committed branch review with a freshly selected model and effort. Use only when explicitly invoked.
argument-hint: "[PR URL or review request]"
disable-model-invocation: true
---

# Goerwin Code Review

Run only when the user explicitly invokes this skill: /goerwin-code-review in Claude Code,
or $goerwin-code-review (or the skill selector) in Codex. A pasted PR URL alone is not an
invocation. Operate in the current conversation until the user has chosen a
model AND effort for this invocation; do not fork this launcher into a reviewer.

The shared helper is scripts/review_pr.py relative to this skill directory.
Invoke it with python3 and an absolute path. It returns JSON. Use argument arrays
or proper shell quoting; never evaluate custom input as shell code.
Install with `make install-skills` so the shared helper symlinks are available.
For development worktree navigation, see `goerwin-wts --help`. The review
launcher handles its own isolated checkouts.

## Resolve the target

Read the invoking repository's instructions, including AGENTS.local.md when
present. Honor its GitHub account preference: pass --github-user USER to resolve.
The helper uses that account's existing gh login without switching the global
account. It never logs or saves tokens. Model-provider authentication belongs
entirely to the launched Codex or Claude Code CLI.

For a PR URL or no input:

~~~sh
python3 /absolute/skill/scripts/review_pr.py resolve "[PR URL]" \
  --cwd /invoking/checkout --output /temporary/unique-target.json
~~~

Omit the positional input completely for no-input resolution. Use a unique
temporary target file for this invocation; don't reuse another request's file.

- A single associated open PR whose GitHub head SHA matches local HEAD is ready.
  Uncommitted changes in the invoking checkout are excluded and left untouched.
- If local HEAD and the PR differ, ask which to review: the GitHub PR version or
  the local committed version. Resolve again with the PR URL and --revision pr
  or --revision local, keeping the original --cwd and account.
- Multiple matching PRs require an explicit PR choice.
- With no PR, propose the current branch against the detected default branch
  and ask for confirmation. If the proposed base is absent or ambiguous, ask.
- Detached HEAD, unclear custom input, or an unavailable GitHub lookup requires
  clarification. Don't substitute a branch review for a failed PR lookup.

Interpret a custom request as a PR or committed head/base comparison and preserve
its review instructions. Resolve concrete refs before launching:

~~~sh
python3 /absolute/skill/scripts/review_pr.py resolve \
  --cwd /invoking/checkout --head feature/foo --base origin/main \
  --instructions "Focus on pagination behavior" \
  --output /temporary/unique-target.json
~~~

Reviewing uncommitted changes needs an explicitly agreed snapshot workflow and
is not implemented here. Unknown repositories must have an existing checkout;
register it with `goerwin-wts register /path/to/checkout`. Never clone automatically.

## Require a fresh model and effort choice

Run the helper's presets command and present the current local presets in the
agent's own response. Do not build or open a Herdr picker. No provider model
catalog or API authentication is needed.

Use the current harness's native question tool when available; otherwise print
numbered choices and wait. Each option is a model/effort pair. If the native UI
has an option limit, split into a model choice and its supported efforts, or
offer grouped presets. Selecting "Astra · High" explicitly selects both values.

Never preselect a previous choice, launch on timeout, or infer a selection from
an earlier invocation. If the target needs clarification, resolve it before
launch. Cancellation or no answer creates neither a worktree nor an agent.

## Launch the selected reviewer

After the user explicitly selects a preset in this invocation:

~~~sh
python3 /absolute/skill/scripts/review_pr.py launch \
  --target-file /temporary/unique-target.json --preset sol-xhigh
~~~

The helper:

- Rechecks the selected revisions and asks for resolution again if they moved.
- Uses Worktrunk's configured placement and normal hooks. It never auto-approves
  hook trust, resets a checkout, cleans files, stashes work, or deletes branches.
- Reuses only a clean, idle review-owned worktree at exactly the selected head
  and base with the same preset. Otherwise it creates a fresh dedicated branch
  and worktree. Multiple reviews of the same PR, even with the same model, may
  run in parallel. Busy, dirty, stale, or unexpected old checkouts are skipped.
- Uses the Herdr adapter to open the proper harness in a fresh tab, select it,
  focus its pane, and bring the app forward. The core skill does not depend on a
  Herdr selection UI. Other tab hosts can add a separate adapter later.
- Passes the frozen target and review guidance directly to the child agent.
  The child must not invoke this launcher recursively.

If launch returns revision_selection_required, ask about the changed revision
and resolve again. Do not launch a saved stale target. If tab creation times out,
inspect status and Herdr before retrying; a tab may already have started.
Focus warnings do not mean launch failed and must not cause another launch.

Report the selected model/effort, checkout, and report path to the user. Existing
review state is informative; it is never a reason to prohibit a parallel review.

## Reports and maintenance

Reports belong in the flat ~/goerwin-code-reviews archive, across all projects.
The helper reserves a unique human-readable Markdown filename:

~~~text
YYYY-MM-DD_project_pr-N-topic_model-effort_HHMMSS.md
2026-10-30_antares_pr-123-pagination_sol-6.1-xhigh_223015.md
~~~

Dates and times in filenames use the machine's local timezone. UTC timestamps,
stable review IDs, repository identity, frozen commits, model and effort live in
YAML frontmatter generated by the helper. An exact filename collision adds _2,
_3, etc.; no random ID is put in the filename. Comparison reviews use their
comparison description instead of a PR number/title.

Each completed review is saved automatically, including no-findings reviews.
Show its findings inline in the reviewer tab and link the saved file; do not ask
whether to save. The launcher only reports the new tab and pending report path.
The original launcher conversation does not receive the review automatically.

Original completed reports are immutable. Later receiving decisions live under
the archive's hidden .receiving directory, linked by review ID and finding ID.
See references/report-format.md for the shared producer/receiver contract.

Reviewer guidance is in references/reviewer.md and is included in the initial
task automatically. Reviews stay local: no source edits, commits, pushes, or
GitHub posting. Later explicit user instructions can authorize a separate action.

Use list --cwd PATH to browse reports for the current project and branch,
list --all-branches for this project's other branches, or list --all for all
projects. Rows include receiving progress. Do not treat a moved HEAD as proof
that all findings are obsolete; the receiving skill checks them against code.

Use status --cwd PATH to inspect runs. An open terminal alone does not mean a
review is active. Completed agents may remain open, so the helper also checks
their processes before reusing a checkout. No automatic cleanup is performed.

The archive contains private run metadata under .runs. An optional --archive
argument or GOERWIN_CODE_REVIEWS_DIR overrides its location. Repository
registrations are shared with goerwin-wts in ~/.config/goerwin-wts/config.json;
the previous goerwin-code-review and review-pr configurations are also read. No existing
configuration or repository-local reports are deleted or moved automatically.

Edit presets.json to maintain the short local model list. Use launch --dry-run
with a resolved target to inspect exact argv without creating a checkout or tab.
