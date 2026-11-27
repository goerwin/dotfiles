---
name: goerwin-address
description: Address review feedback from a PR, a saved review report, or pasted text; verify each finding, fix what meets the bar, and draft replies. Use only when explicitly invoked.
argument-hint: "[PR URL | report path | pasted feedback]"
disable-model-invocation: true
---

# Goerwin Address

<!-- include: rules.md -->

## Gather feedback

Feedback comes from a PR URL, a saved report path, or pasted text. With
nothing given, use the current branch's [PR threads](#pr-threads) plus the
latest report for this branch in `~/goerwin-reviews/<project>/`; ask only if
neither exists. For a PR, also read its conversation
(`gh pr view URL --comments`) and treat only comments that ask for a change
as findings.

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
edits. Show the code changes and numbered outcomes in the reply. If the
feedback came from a saved report, append an `## Outcomes` section to it. For
PR threads, draft replies as described in [PR threads](#pr-threads).

<!-- include: criteria.md -->

<!-- include: pr-threads.md -->
