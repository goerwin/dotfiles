---
name: goerwin-review
description: Code review, multi-model council reviews, addressing review feedback, architecture reviews, and mutation testing of a change's tests, with saved reports. Use only when explicitly invoked.
argument-hint: "[review | council … | address … | architecture [folder] | mutation]"
disable-model-invocation: true
---

# Goerwin Review

## Choose the mode

| The request has | Mode |
|---|---|
| Nothing, "review", a PR URL, or a branch | Code review |
| "council", or a model to review with | Council |
| "address", "feedback", "comments", pasted feedback, or a report path | Addressing feedback |
| "architecture", optionally with a folder | Architecture: follow `references/architecture.md` |
| "mutation", or whether the tests are useful | Mutation: follow `references/mutation.md` |

Ask when the request matches several modes or none.

## Rules for every mode

- **Criteria:** reviews follow `references/criteria.md`. Give delegates its
  absolute path: `~/.agents/skills/goerwin-review/references/criteria.md`.
- **Git:** commit as needed, in small commits with short conventional subjects
  (`fix: keep cursors stable across pages`). Never squash or rewrite history
  unless asked. Never stash, reset, or discard work you didn't make.
- **Publishing:** ask before pushing or posting anything to GitHub (replies,
  comments, PR description edits). The request names the signed-in account
  (`gh api user --jq .login`) and where each item lands. Push only to the PR's
  branch, never the default branch.
- **Worktrees:** create, switch, and remove them only with `wt`, never
  `git worktree add`.
- **Scope:** a PR URL must belong to the current checkout's repository; never
  clone.

## Reports

Save every code review, council run, architecture review, and mutation run to
`~/goerwin-reviews/<project>/YYYY-MM-DD-<topic>.md`, where `<project>` is the
repository folder name; add `-2`, `-3`, … if the name is taken. Start with the
mode, repository, branch, HEAD SHA, base or scope, and each model with its
effort, then the findings in the format from `references/criteria.md`.

Show the full report in the reply, then link the file. When feedback from a
saved report is addressed, append an `## Outcomes` section to that same file.

## Code review

Review in the current checkout without editing code. Fetch, then compare the
branch with its PR's base (`gh pr view --json url,baseRefName`), or with the
remote default branch when there is no PR. Diff from the merge base
(`git diff $(git merge-base origin/BASE HEAD)`) so uncommitted work is
included.

For a PR, read its description and comments (`gh pr view URL --comments`) and
don't repeat existing findings. Read callers and surrounding code to establish
behavior, and run focused checks when they establish a finding.

## Council

Two or three delegates review or give feedback, usually on code but also on
plans or designs.

### Before starting

- Make sure you have the intent, goal, and context. Ask for anything missing.
- If there is a PR, read its unresolved review comments first (see
  [PR threads](#pr-threads)). Fix the valid ones; for the rest, draft a short
  pushback and show it. Posting follows the publishing rule.
- Fix other known issues and run relevant checks, so the council reviews the
  current implementation. Don't defer known fixes until reviews return.
- Pick the delegates: each a model from a different provider, by default the
  latest frontier model of each (e.g. GPT Sol, Claude Opus, Gemini Pro) at high
  effort. Use the members the user names; one named model is a council of one.
- Show the number of delegates and, for each, the provider, exact model
  version, effort, and where it runs (internal subagent or Herdr tab), plus the
  rubric and round limit. Wait for confirmation.

### Running delegates

Give each delegate the request, intent, context, the review base, the criteria
path, and the rubric. Delegates are read-only and don't start other agents.
For code reviews, ask each for findings in the criteria format and a score out
of 10.

Use the harness's own subagents when they support the model. Otherwise start
the delegate as an interactive agent with `hc`, shown as a tab in the current
Herdr space (`.space` from `herdr-app status`; drop the label if Herdr isn't
open). Write its prompt to a file and have it write its findings to another:

```sh
hc run --bg --name council-sol --cwd "$PWD" --label herdr.space=SPACE \
  codex --no-daemon --model MODEL -c 'model_reasoning_effort="high"' \
  "Read /tmp/council/sol-prompt.md and follow it."
env -u CLAUDECODE -u CLAUDE_CODE_EFFORT_LEVEL hc run --bg --name council-opus --cwd "$PWD" \
  --label herdr.space=SPACE claude --model MODEL --effort high "Read /tmp/council/opus-prompt.md and follow it."
hc wait --children any
```

Wait with `hc wait`, never sleep; a timeout is a check-in, not a failure. If a
delegate stops without its findings file, read its screen (`hc read NAME`)
before deciding anything, and never start a duplicate. When you have its
results, `hc kill NAME; hc rm NAME`.

While delegates run:

- Don't wait idle. Check each result against the code as it arrives and decide
  what to fix while the others run.
- Don't edit files while a delegate is still reviewing the same checkout.
- If the user marks a delegate as non-blocking, don't wait for it. Treat a late
  result as feedback and don't record its score.

### Rounds

Each full review pass is one round; a fresh review after fixes starts a new
one. Apply the recommendations you agree with, then request a fresh review.
Repeat until all delegates are satisfied, up to 5 rounds unless the user sets
another limit. If findings remain at the limit, stop and list them. Don't let
repeated reviews cause scope creep; keep the scope limited.

### Finish

Summarize the useful findings, disagreements, and what was applied or pushed
back, and save one report for the whole run with this table:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| GPT Sol | 8/10 | 10/10 |
```

If a delegate gives no score, write `no score`; never invent one. The table
goes in the reply and the report, never on GitHub.

If applicable, offer to push the commits and update the PR description. Keep
the description short, precise, and useful for readers: what changed and why.

## Addressing feedback

Feedback comes from a PR URL, a saved report path, or pasted text. With
nothing given, use the current branch's PR threads plus the latest saved
report for this branch; ask only if neither exists. For a PR, also read its
conversation (`gh pr view URL --comments`) and treat only comments that ask for
a change as findings.

For each finding, establish the expected behavior, then verify the claim
against current code, callers, and tests. Group duplicates by their real
underlying issue; the same file and line alone isn't a duplicate. Give each one
outcome:

- **Applied:** correct and a concrete improvement. Make a focused root-cause
  fix with existing patterns. An issue already fixed counts, with evidence.
- **Pushed back:** incorrect, speculative, out of scope, preference without
  benefit, a workaround, a test-only change that forces a pass, or a change of
  intent. Explain with evidence; suggest a follow-up for valid out-of-scope
  ideas.
- **Waiting:** needs facts only the user or reviewer has. Ask a concrete
  question.

Reproduce bugs and run focused checks when practical, and preserve unrelated
edits. Show the code changes and numbered outcomes in the reply, and append
the outcomes to the report if the feedback came from one.

For PR threads, draft one reply per thread. Replies sound like a person:
brief, direct, casual, no hedging, no em dashes. A waiting reply is the
question for the reviewer. Show them all before anything leaves the machine:

```text
Posting as @<login>:
1. menu.tsx:62 (applied) Good catch, the playground now switches rows with the mode.
2. menu.tsx:118 (pushed back) I'd keep this one. Splitting it would change the API this PR adds.
3. menu.tsx:140 (waiting) Should multiple selection keep the order users clicked?
```

Then ask once: push, reply (all or some), both, or skip. Push before replying
so replies can reference the fix. Confirm the posted URLs.

### PR threads

List unresolved threads. Skip a thread only when the signed-in account
replied after someone else's last comment; threads it started stay open:

```sh
gh api graphql -f owner=OWNER -f repo=REPO -F number=N -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
    reviewThreads(first: 100) { nodes { id isResolved isOutdated path line
      comments(first: 50) { nodes { author { login } body url } } } } } } }'
```

Reply to a thread, or post a top-level comment:

```sh
gh api graphql -f thread=THREAD_ID -f body="$BODY" -f query='
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url } } }'
gh pr comment URL --body "$BODY"
```

If posting stops partway, list what was already posted and retry only the
rest.
