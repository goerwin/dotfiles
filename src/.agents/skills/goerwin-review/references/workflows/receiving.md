# Receiving review

Work in the invoking conversation with `scripts/receiving.py`.

## 1. Choose the feedback

Accept a PR URL, saved report paths, pasted feedback, or nothing.

**Nothing:** run `receiving.py options --cwd /current/checkout` and show its
`choices` as a numbered list, saying what each will do: the branch PR's open
GitHub threads (plus reviews matching the current code), reviews matching the
current code, or older reviews to pick from (show project, skill/rubric,
model/effort, date, reviewed SHA, remaining/waiting). Wait for the choice;
never pick for the user. With no choices, offer `list --all-branches`, or
`list --all` across projects.

**PR URL** (or the `github` choice): import the open threads, then prepare
them first and this branch's current reviews after them:

~~~sh
python3 /abs/skill/scripts/receiving.py github-threads --cwd /current/checkout --pr URL
python3 /abs/skill/scripts/receiving.py prepare --cwd /current/checkout \
  --review /path/first.md --review /path/second.md
~~~

`github-threads` saves unresolved threads whose last comment isn't yours as a
report (one `### F<n>` per thread, with its `thread` ID) and returns the
`viewer` login that would post replies. Also read the PR's conversation
(`gh pr view URL --comments`) and treat only comments asking for a change as
extra findings.

**Pasted feedback:** save it verbatim to a temporary file and pass
`--text-file PATH` instead of `--review`. Put several unstructured claims under
`### F1:` / `### F2:` headings without rewriting them. It is evaluated but not
recorded (`recordable: false`).

| Status | Ask the user |
|---|---|
| `repository_selection_required` | Which checkout to use; rerun from there. |
| `target_selection_required` | Which target's reports to receive now. |
| `branch_confirmation_required` | Whether to switch; `--confirm-branch` opens the reviewed branch's worktree (reused, or created through Worktrunk and focused in Herdr). |
| `branch_selection_required` | Which development branch receives the fixes; pass `--branch`. |

On `ready`, show the summary: the returned `cwd`, branch, HEAD, reports and
active findings, stale reviews, and that fixes stay local until step 4.
Confirming it authorizes the local fixes and recording. Work in the returned
`cwd`; never stash, reset, discard work, or apply feedback to an unrelated
checkout.

## 2. Address

Follow `references/standards.md` and `references/workflows/addressing.md`, then
show the code changes and numbered outcomes inline.

## 3. Record

For recordable sessions, write the outcomes to a temporary file and run:

~~~sh
python3 /abs/skill/scripts/receiving.py record --cwd /prepared/cwd \
  --review /path/first.md --review /path/second.md --outcomes /tmp/outcomes.json
~~~

It checks that every active finding is covered exactly once and appends the
outcomes to each report's `*.receiving.md` sidecar; originals stay unchanged.
Link the sidecars.

## 4. Preview, then commit, push, or reply

For GitHub threads, draft one reply per thread and show them all before
anything leaves the machine. Replies sound like a person: brief, direct,
casual, no hedging, no em dashes. A waiting reply is the question for the
reviewer. Number them with where they land and who posts them:

~~~text
Posting as @<viewer>:
1. menu-playground.tsx:62 (applied) Good catch, the playground now switches rows with the mode.
2. menu.tsx:118 (pushed back) I'd keep this one. Splitting it would change the API this PR adds.
3. menu.tsx:140 (waiting) Should multiple selection keep the order users clicked? Didn't want to guess.
~~~

Then ask once: commit, push, reply (all or some), any combination, or skip.
Commit with a short conventional message; push only to the PR's branch, never
`main`; push before replying so replies can reference the fix. Post with:

~~~sh
python3 /abs/skill/scripts/receiving.py reply --cwd /current/checkout --pr URL \
  --replies /tmp/replies.json   # [{"thread": "PRRT_…", "body": "…"}, {"thread": null, "body": "…"}]
~~~

`thread: null` posts a PR comment. Confirm the posted URLs and author. If it
stops partway, it lists what was already posted; retry only the rest.
