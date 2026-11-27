## PR threads

List unresolved threads. Skip a thread only when the signed-in account
replied after someone else's last comment; threads it started stay open:

```sh
gh api graphql -f owner=OWNER -f repo=REPO -F number=N -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
    reviewThreads(first: 100) { nodes { id isResolved isOutdated path line
      comments(first: 50) { nodes { author { login } body url } } } } } } }'
```

Draft one reply per thread. A waiting reply is the question for the reviewer.
Each reply starts with its outcome label, `(applied)`, `(pushed back)`, or
`(waiting)`, so reviewers see the position at a glance. Show them all before
anything leaves the machine:

```text
Posting as @<login>:
1. menu.tsx:62 (applied) Fixed
2. menu.tsx:95 (applied) Done, the playground had the same issue so it switches rows with the mode now too
3. menu.tsx:118 (pushed back) I'd keep this one, splitting it would change the API this PR adds
4. menu.tsx:140 (waiting) Should multiple selection keep the order users clicked?
```

Then ask once: push, reply (all or some), both, or skip. Push before replying
so replies can reference the fix. Reply to a thread, or post a top-level
comment:

```sh
gh api graphql -f thread=THREAD_ID -f body="$BODY" -f query='
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url } } }'
gh pr comment URL --body "$BODY"
```

Confirm the posted URLs. If posting stops partway, list what was already
posted and retry only the rest.
