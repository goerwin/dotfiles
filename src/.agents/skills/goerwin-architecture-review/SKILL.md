---
name: goerwin-architecture-review
description: >-
  Review a codebase and look for improvement opportunities.
  Use only when the user explicitly calls this skill.
disable-model-invocation: true
---

# Codebase Architecture Review

Review the codebase and look for refactoring opportunities, code duplication, hacky solutions or implementations,
unused code, poor design decisions, and other risks that may make the code unstable or fragile.

## Mode

By default, only report findings. Do not change code unless the user asks for it.

## Scope

For large codebases, ask the user for a scope (a folder, feature, or layer) or focus on the areas with the
highest impact first instead of reviewing everything at once.

## Understand the codebase first

Before judging anything, map the folder structure, entry points, and existing conventions. Respect the
architecture the project already uses instead of replacing it with a different style.

## Folder or feature-scoped architecture

If the codebase is organized by folder or feature, each folder should only contain code related to its scope.
For example, a `Signin` folder should not contain code unrelated to sign-in, and a `Database` folder should not
contain business logic or other unrelated or unused logic.

The main goal is to detect code that doesn't belong to a particular feature and move it where it belongs.

## Dependency direction

- Shared or lower-level code (e.g. `Database`, `UI`) must not import from features.
- Features should not import each other's internals. Code needed by both belongs in a shared place.
- Flag circular imports.

## Shared code

Reused code should live in a higher-level folder. At minimum, it should be in the closest common parent of the
features or folders that use it. In small projects, a single `shared` folder is enough. It doesn't have to be
called `shared`; the feature name, a grouping `utils`, `tools`, etc. or a more suitable or simpler
name may work better.

The goal is to make the folder structure easy to scan, so you can understand how a folder or feature may affect
the rest of the code. For example, a `Database` folder at the root suggests that sibling folders and their
subfolders may use it. A `UI` folder inside a `Signin` folder suggests that those UI components are only used
by `Signin`.

Only move code to a shared folder when two or more places use it. Code used in a single place should stay next
to where it's used.

## Hacky solutions or implementations

Identify implementations that could be simpler, more logical, or easier to work with, especially when the
platform, framework, or language already offers a native way to do it. Prefer solutions that are more
maintainable, robust, and aligned with high standards. For example:

- Custom code that reimplements a built-in platform or library feature.
- Workarounds such as timeouts, retries, or flags that hide a bug instead of fixing it.
- Type casts, suppressed errors, or disabled lint rules used to silence real problems.

## Unused code

Before reporting code as unused, check for indirect usages such as dynamic imports, config files, routes,
public exports, scripts, and tests.

## Documentation

Flag documentation that describes unrelated or unused features. More documentation is not better documentation.
Fixes and minor code changes often get over-explained in READMEs and other public-facing docs, which should stay
high-level and avoid implementation details.

## Comments

Flag unnecessary comments that explain code that is already simple and easy to understand.

## Report format

Group findings by severity (high, medium, low). For each finding, include:

- File path(s)
- What the problem is
- Why it matters
- Suggested fix

If there are findings, ask whether to save them. If yes, follow `~/.local/share/goerwin-tools/saving.md`
with `--skill goerwin-architecture-review` and `--scope` set to the reviewed folder (`.` for the whole
repository), using `high`/`medium`/`low` as each finding's severity.

## Applying fixes

When the user asks to apply fixes:

- Make small, focused changes, one finding at a time.
- Run type checks, linters, and tests after each change when appropriate.
  Skip them, for example, for documentation-only changes, unless the documentation
  is covered by the configured test or lint rules (e.g. a Markdown linter).
