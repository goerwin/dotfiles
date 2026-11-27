---
name: goerwin-review
description: Review a branch, PR, or uncommitted work in the current checkout and save a findings report. Use only when explicitly invoked.
argument-hint: "[PR URL | branch] [adversarial | design]"
disable-model-invocation: true
---

# Goerwin Review

Review in the current checkout without editing code. A PR URL must belong to
this checkout's repository; never clone.

<!-- include: base.md -->

## Review

For a PR, read its description and comments (`gh pr view URL --comments`) and
don't repeat existing findings. Read callers and surrounding code to establish
behavior, and run focused checks when they establish a finding.

<!-- include: criteria.md -->

<!-- include: rubrics.md -->

<!-- include: reports.md -->
