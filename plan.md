# Plan: Consolidate the review skills into `goerwin-review`

## Objective

Replace `goerwin-code-review`, `goerwin-receiving-code-review`,
`goerwin-review-loop`, and `goerwin-architecture-review` with one explicitly
invoked `goerwin-review` skill. Keep `goerwin-handoff` separate. Remove
duplicated review rules and report formats, and keep every file short.

## Structure

```text
src/.agents/skills/goerwin-review/
  SKILL.md                     # routing, summary fields, confirmation rule
  agents/openai.yaml
  references/
    standards.md               # shared review rules
    findings.md                # F-format and saving (replaces saving.md)
    reviewer.md                # isolated reviewer task
    rubrics/default.md
    rubrics/adversarial.md
    workflows/code-review.md
    workflows/receiving.md     # choose feedback, preview, commit/push/reply
    workflows/addressing.md    # verify, address, outcomes (shared with the loop)
    workflows/review-loop.md
    workflows/architecture.md
  scripts/
    review.py                  # was review_pr.py; adds `save`
    receiving.py
    review_loop.py
    review_tools/              # review_store, targets, github_threads
    goerwin_tools -> ~/.local/lib/goerwin_tools
  tests/
```

## Decisions

- Routing: code review is the default (bare call, PR URL, branch, "in isolation
  with <model>"); receiving needs "address/receive/feedback/reply/comments" or
  saved report paths; the loop needs "loop" (or "resume" for a waiting loop);
  architecture needs "architecture" plus an optional folder. Ask when a request
  matches several modes or none.
- Every mode shows one summary after its read-only helper resolves the target
  and waits for confirmation before editing, writing, or launching. Existing
  up-front confirmations fold into it; commit/push/reply and squash gates stay.
  Handoff gets its own shorter summary before launch.
- One finding format everywhere, including architecture output in chat.
  Rubrics and modes keep their own severity scales.
- Rubrics keep only what to look for, what to skip, and severity; shared rules
  live in `standards.md`. The loop implementer gets `standards.md` and
  `addressing.md` only.
- `goerwin-review save` becomes `review.py save`; `~/.local/bin/goerwin-review`
  is retired. `harness`, `presets.json`, and the worktree/Herdr modules stay in
  `~/.local/lib/goerwin_tools`.
- Report skill IDs stay `goerwin-code-review` and `goerwin-architecture-review`.

## Safeguards to preserve

- Code review: frozen revisions, existing-comment checks, read-only review,
  report completion.
- Receiving: user picks feedback, replies are previewed, ask before commit,
  push, or reply.
- Loop: confirmation boundary, no push, waiting/resume, single final squash.
- Architecture: report-only unless asked for fixes.

## Installation

The skills installer retires the three old installed skill copies and only the
Claude/Codex links pointing to them, warning about anything else. The tools
installer removes `~/.local/bin/goerwin-review` only when it carries the
entry-point marker. Library and docs syncs already delete removed files.

## Verification

Run every test suite from its new location, install into a temporary
`GOERWIN_SKILLS_HOME`, and search for stale paths. Don't launch handoffs, post
to GitHub, or push.
