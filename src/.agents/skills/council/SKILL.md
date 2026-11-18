---
name: goerwin-council
description: Council work with multiple agents. Use only when explicitly invoked.
disable-model-invocation: true
---

# Council

## Before starting

- Make sure you have the intent, goal, and any other context needed. Ask the
  user for anything missing.
- Flag anything the user needs to address, and preview the models you will use.
- If there is a PR, read its unresolved review comments before delegating.
  Fix the ones that are valid and worth addressing. For the rest, draft a short
  pushback explaining why, and show it to the user; do not post replies without
  permission.
- Fix other known issues and run relevant checks so the council reviews the
  current implementation. Do not defer known fixes until reviews return.

## Delegates

Use two or three delegates, usually for review or feedback. Each should be a
strong model from a different provider, at high reasoning effort. Use the
council members the user names; otherwise pick the latest flagship from each
provider (e.g. Claude Opus, GPT Sol).

Give each delegate the request and relevant context. Keep review and feedback
work read-only. For code reviews, tell delegates to read and apply
`~/.agents/skills/goerwin-review/references/standards.md` and
`~/.agents/skills/goerwin-review/references/rubrics/default.md`.

Summarize the useful findings, disagreements, and recommended next steps.

## While delegates run

- Do not wait idle. Check each result against the code as it arrives and
  decide what to fix while the others run.
- Do not edit files while a delegate is still reviewing the same checkout.
- If the user marks a delegate as non-blocking, do not wait for it. Treat a
  late result as feedback and do not record its score.

## Rounds and scoring

For code reviews, ask each delegate for a score out of 10. Each full review
pass is one round; a fresh review after fixes starts a new round.

Apply the recommendations you agree with, then request a fresh review. Repeat
until all delegates are satisfied, up to 5 rounds unless the user sets another
limit. If findings remain at the limit, stop and list them for the user. Do not
let repeated reviews cause scope creep; actively keep the scope limited.

## Git and PRs

You may commit freely. Never push or change a PR without the user's
permission.

When the work is done, if applicable, offer the user the option to push the
commits and update the PR description. Keep the description short, precise,
and useful for readers: what changed and why. Do not include council results.

## Reporting

Report results only in your reply, never in a PR. Use this format:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| GPT Sol | 8/10 | 10/10 |
| Gemini Pro | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Never invent one.
