---
name: goerwin-architecture
description: Review a codebase or folder for structure, dependency direction, duplication, hacky or unused code, and other design risks, with a saved findings report. Use only when explicitly invoked.
argument-hint: "[folder]"
disable-model-invocation: true
---

# Goerwin Architecture

Review the codebase for refactoring opportunities, duplication, hacky
implementations, unused code, poor design decisions, and other risks that make
it unstable or fragile. Only report findings; change code only when the user
asks.

For large codebases, ask for a scope (a folder, feature, or layer) or start
with the highest-impact areas.

<!-- include: rules.md -->

## Understand the codebase first

Map the folder structure, entry points, and existing conventions before judging
anything. Respect the architecture the project already uses instead of
replacing it with a different style.

## What to look for

Everything under [What to report](#what-to-report), applied to existing code
(pre-existing issues are in scope here), plus:

- **Scope:** in a codebase organized by folder or feature, each folder holds only code for its scope. A `Signin` folder shouldn't contain unrelated code; a `Database` folder shouldn't contain business logic.
- **Dependency direction:** shared or lower-level code (e.g. `Database`, `UI`) must not import from features; features don't import each other's internals; flag circular imports.
- **Shared code:** code used by two or more places lives in their closest common parent (in small projects, one shared folder). Code used in one place stays next to it, so the layout shows reach at a glance.
- **Reimplemented features:** code that reimplements a platform, framework, or library feature. Prefer the native solution.
- **Unused code:** check indirect usages first (dynamic imports, config files, routes, public exports, scripts, tests).
- **Stale docs:** docs for unrelated or unused features.

Use severity high, medium, or low, list every affected path, and record the
scope (`.` for the whole repository) in the report.

## Applying fixes

When the user asks, make small, focused changes one finding at a time. Run type
checks, linters, and tests after each change when appropriate; skip them for
documentation-only changes unless the docs are covered by configured checks.

<!-- include: criteria.md -->

<!-- include: reports.md -->
