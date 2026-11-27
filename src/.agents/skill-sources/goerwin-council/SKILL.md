---
name: goerwin-council
description: Run models from different providers as a review council over code, plans, or designs, fixing findings between rounds until they're satisfied. Use only when explicitly invoked.
argument-hint: "[models…] [adversarial | design]"
disable-model-invocation: true
---

# Goerwin Council

Delegates from different providers review the work; you verify their
findings, fix what meets the feedback bar, and run fresh rounds until they're
satisfied.

<!-- include: rules.md -->

<!-- include: base.md -->

## Existing PR feedback

If there is a PR, read its unresolved review comments before the first round
(see [PR threads](#pr-threads)). Fix the ones that meet the
[feedback bar](#standards); for the rest, draft a short pushback and show it.

<!-- include: council.md -->

## After the council

If applicable, offer to push the commits and update the PR description. Keep
the description short, precise, and useful for readers: what changed and why.

<!-- include: criteria.md -->

<!-- include: rubrics.md -->

<!-- include: reports.md -->

<!-- include: pr-threads.md -->
