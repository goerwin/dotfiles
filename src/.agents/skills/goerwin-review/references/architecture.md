# Architecture review

Review the codebase for refactoring opportunities, duplication, hacky
implementations, unused code, poor design decisions, and other risks that make
it unstable or fragile. Only report findings; change code only when the user
asks.

For large codebases, ask for a scope (a folder, feature, or layer) or start
with the highest-impact areas.

## Understand the codebase first

Map the folder structure, entry points, and existing conventions before judging
anything. Respect the architecture the project already uses instead of
replacing it with a different style.

## What to look for

- **Scope:** in a codebase organized by folder or feature, each folder holds only code for its scope. A `Signin` folder shouldn't contain unrelated code; a `Database` folder shouldn't contain business logic.
- **Dependency direction:** shared or lower-level code (e.g. `Database`, `UI`) must not import from features; features don't import each other's internals; flag circular imports.
- **Shared code:** code used by two or more places lives in their closest common parent (in small projects, one shared folder). Code used in one place stays next to it, so the layout shows reach at a glance.
- **Hacky implementations:** code that reimplements a platform, framework, or library feature; timeouts, retries, or flags that hide a bug; casts, suppressed errors, or disabled lint rules that silence real problems. Prefer the simpler, native, maintainable solution.
- **Unused code:** check indirect usages first (dynamic imports, config files, routes, public exports, scripts, tests).
- **Documentation:** flag docs for unrelated or unused features. READMEs and public docs stay high-level; fixes and minor changes are often over-explained.
- **Comments** that restate self-explanatory code or narrate earlier implementations.
- **AI slop:** filler comments or code, and leftovers of an earlier pass such as compatibility shims, fallbacks, aliases, or dual paths with no real migration.

## Report

Use the findings format from `criteria.md` with severity high, medium, or low,
listing every affected path. Save it like any other report, with the scope
(`.` for the whole repository).

## Applying fixes

When the user asks, make small, focused changes one finding at a time. Run type
checks, linters, and tests after each change when appropriate; skip them for
documentation-only changes unless the docs are covered by configured checks.
