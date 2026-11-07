# Architecture review

Review the codebase for refactoring opportunities, duplication, hacky
implementations, unused code, poor design decisions, and other risks that make
it unstable or fragile. Only report findings; change code only when the user
asks.

For large codebases, ask for a scope (a folder, feature, or layer) or start
with the highest-impact areas. The summary covers the repository, branch, HEAD,
and scope, and notes that nothing is written unless the user chooses to save.

## Understand the codebase first

Map the folder structure, entry points, and existing conventions before judging
anything. Respect the architecture the project already uses instead of
replacing it with a different style.

## What to look for

- **Scope:** in a codebase organized by folder or feature, each folder holds only code for its scope. A `Signin` folder shouldn't contain unrelated code; a `Database` folder shouldn't contain business logic. Move code that doesn't belong.
- **Dependency direction:** shared or lower-level code (e.g. `Database`, `UI`) must not import from features; features don't import each other's internals; flag circular imports.
- **Shared code:** code used by two or more places lives in their closest common parent (in small projects, one shared folder, under whatever name fits). Code used in one place stays next to it. The layout should show reach at a glance: a root `Database` folder may be used by its siblings; a `UI` folder inside `Signin` only by `Signin`.
- **Hacky implementations:** code that reimplements a platform, framework, or library feature; timeouts, retries, or flags that hide a bug; casts, suppressed errors, or disabled lint rules that silence real problems. Prefer the simpler, native, maintainable solution.
- **Unused code:** check indirect usages first (dynamic imports, config files, routes, public exports, scripts, tests).
- **Documentation:** flag docs for unrelated or unused features. READMEs and public docs stay high-level; fixes and minor changes are often over-explained.
- **Comments** that explain code that is already simple.

## Report

Use `references/findings.md` with severity high, medium, or low, listing every
affected path. If there are findings, ask whether to save them; if yes, save
with `--skill goerwin-architecture-review --scope PATH` (`.` for the whole
repository).

## Applying fixes

When the user asks, make small, focused changes one finding at a time. Run type
checks, linters, and tests after each change when appropriate; skip them for
documentation-only changes unless the docs are covered by configured checks
(e.g. a Markdown linter).
