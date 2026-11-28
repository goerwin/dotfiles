---
name: goerwin-babysit
description: Take work to a ready state in one run; implement the task if there's no work yet, address PR feedback, loop reviews by models from different providers with fixes, wait for CI, and finish with a draft PR or pushed replies. Use only when explicitly invoked.
argument-hint: "[task | plan | PR URL | address pr comments] [models…]"
disable-model-invocation: true
---

# Goerwin Babysit

Take the current work to a ready state in one run. Make the technical
decisions yourself; ask the user only about intent, approach, and facts you
can't find, batched as described in the [review loop](#review-loop).

<!-- include: rules.md -->

## Starting point

Use what the user gave; with nothing given, use the current branch and its PR.

- **A task with no work yet:** create a branch from the up-to-date default
  branch, implement the task following the [standards](#standards), and run
  the project's checks.
- **Work on a branch without a PR:** start from it. If the work is on the
  default branch, ask for a branch name.
- **Only PR feedback** (e.g. "address pr comments", "fix the Copilot
  comments"): use the PR given, or the current branch's PR. Address its
  [feedback](#pr-feedback), skip the review loop and the mutation check, run
  the project's checks, then [finish](#finish). Apply the [fix sweep](#standards)
  before drafting replies. A finding that needs a bigger change is a
  question, not a fix.
- **A PR:** address its feedback first (see [PR feedback](#pr-feedback)).
- **A plan or design without code:** run the review loop on the plan, then
  stop with the revised plan and the report.

Make sure you have the intent, goal, and context; ask for anything missing in
one batch.

<!-- include: base.md -->

## PR feedback

List unresolved threads. Skip a thread only when the signed-in account
replied after someone else's last comment; threads it started stay open:

```sh
gh api graphql -f owner=OWNER -f repo=REPO -F number=N -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
    reviewThreads(first: 100) { nodes { id isResolved isOutdated path line
      comments(first: 50) { nodes { author { login } body url } } } } } } }'
```

Also read the conversation (`gh pr view URL --comments`) and treat only
comments that ask for a change as findings. Give each finding an
[outcome](#outcomes). Apply fixes and sweep the shared contract before
drafting replies (see [Replies](#replies)); replies are posted at the
[finish](#finish).

## Outcomes

Verify each finding against current code, callers, and tests. Group
duplicates by their real underlying issue; the same file and line alone isn't
a duplicate. Give each one outcome:

- **Applied:** meets the [feedback bar](#standards). Make a focused fix. An
  issue already fixed counts, with evidence.
- **Pushed back:** below the feedback bar, incorrect, speculative, out of
  scope, a change of intent, or a fix the [standards](#standards) rule out.
  Explain with evidence; suggest a follow-up for valid out-of-scope ideas.
- **Waiting:** needs facts only the user or reviewer has. Ask a concrete
  question.

Reproduce bugs and run focused checks when practical, and preserve unrelated
edits.

## Review loop

1. Fix known issues and run relevant checks first, so reviewers see the
   current implementation. For new code, list every promise in its docs and
   types. Cover combinations with one or two stress fixtures and invariant
   assertions (no overlap, every control reachable, nothing dangling); extend
   existing tests without duplicate coverage. Run the [probes](#probes)
   against the implementation before round 1.
2. Pick and confirm the [reviewers](#reviewers), with the round limit.
3. In round 1 with two or more reviewers, give one the design rubric and one
   the adversarial rubric; alternate the rest. With one reviewer, use design
   plus the probes. Later rounds use the criteria and adversarial rubric.
4. Give each finding an [outcome](#outcomes), apply the applied ones, and
   sweep each fix before the next round. Round 2 onward confirms fixes. Only
   critical, high, or medium findings justify another full round; fix and
   verify low findings locally or propose follow-ups. Blocking counts as high;
   suggestion as low. Stop when no full round is needed, or after 5 rounds
   unless the user sets another limit. List findings left at the limit. Don't
   let repeated reviews cause scope creep.
5. Answer questions from code, docs, and history when you can. Ask the user
   the rest in one batch per round, and keep fixing unrelated findings while
   you wait. A finding that would change the approach or the intent is a
   question, not a fix.
6. If the branch adds or edits tests, run the
   [mutation check](#mutation-check) on them, and fix survivors and bloat that
   meet the feedback bar.

## Finish

1. The project's type checks, linters, and tests pass.
2. Save one report with the reviewers table, the outcomes, and any mutation
   tables.
3. Compare the current or draft PR description, changeset, and docs against
   the final code.
   Show everything that would leave the machine, then ask once:
   - **No PR:** push and open a draft PR (`gh pr create --draft`) with a
     short, precise description: what changed and why.
   - **A PR:** push, post the drafted replies (all or some), and update the
     description if the change made it wrong. Push before replying so replies
     can reference the fix.
4. Wait for CI (`gh pr checks --watch`). Fix failures the branch causes and
   push the fixes to the same branch; the approved push covers them. Report
   failures the branch didn't cause instead of working around them.

## Replies

Draft one reply per thread. A waiting reply is the question for the reviewer.
Each reply starts with its outcome label, `(applied)`, `(pushed back)`, or
`(waiting)`, so reviewers see the position at a glance:

```text
Posting as @<login>:
1. menu.tsx:62 (applied) Fixed
2. menu.tsx:95 (applied) Done, the playground had the same issue so it switches rows with the mode now too
3. menu.tsx:118 (pushed back) I'd keep this one, splitting it would change the API this PR adds
4. menu.tsx:140 (waiting) Should multiple selection keep the order users clicked?
```

Reply to a thread, or post a top-level comment:

```sh
gh api graphql -f thread=THREAD_ID -f body="$BODY" -f query='
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url } } }'
gh pr comment URL --body "$BODY"
```

Confirm the posted URLs. If posting stops partway, list what was already
posted and retry only the rest.

<!-- include: reviewers.md -->

<!-- include: mutation.md -->

<!-- include: criteria.md -->

<!-- include: probes.md -->

<!-- include: rubrics.md -->

<!-- include: reports.md -->
