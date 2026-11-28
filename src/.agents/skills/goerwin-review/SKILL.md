---
name: goerwin-review
description: Review a branch, PR, uncommitted work, or plan, by this session or by several models from different providers, and save a findings report. Reviews only; never fixes. Use only when explicitly invoked.
argument-hint: "[PR URL | branch | plan] [models…] [adversarial | design]"
disable-model-invocation: true
---

# Goerwin Review

Review without editing anything. This session reviews by default; when the
user asks for more reviewers or names models, run the
[reviewers](#reviewers) and merge their findings into one report. A PR URL
must belong to this checkout's repository; never clone.

<!-- include: base.md -->

## Review

For a PR, read its description and comments (`gh pr view URL --comments`) and
don't repeat existing findings. Read callers and surrounding code to establish
behavior, and run focused checks when they establish a finding. For a plan or
design, judge it against the goal and cite its sections instead of file
paths.

<!-- include: reviewers.md -->

<!-- include: criteria.md -->

<!-- include: probes.md -->

<!-- include: rubrics.md -->

<!-- include: reports.md -->
