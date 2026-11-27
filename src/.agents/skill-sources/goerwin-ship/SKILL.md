---
name: goerwin-ship
description: Take a finished local branch to a draft PR in one run, through a council design round, council review rounds, and a mutation check of its tests. Use only when explicitly invoked.
argument-hint: "[models…]"
disable-model-invocation: true
---

# Goerwin Ship

Take a finished local branch to a draft PR in one run.

<!-- include: rules.md -->

<!-- include: base.md -->

## Steps

1. **Branch:** if the work is on the default branch, ask for a branch name.
2. **Design round:** run the [council](#council); its first round uses the
   design rubric.
3. **Review rounds:** later rounds use the criteria plus the adversarial
   rubric. All rounds share the round limit.
4. **Tests:** if the branch adds or edits tests, run the
   [mutation check](#mutation-check) on them, and fix survivors and bloat that
   meet the [feedback bar](#standards).
5. **Finish:** the project's type checks, linters, and tests pass. Save one
   report with the council table and the mutation tables. Then ask to push and
   open a draft PR (`gh pr create --draft`) with a short, precise description:
   what changed and why.

<!-- include: council.md -->

<!-- include: mutation.md -->

<!-- include: criteria.md -->

<!-- include: rubrics.md -->

<!-- include: reports.md -->
