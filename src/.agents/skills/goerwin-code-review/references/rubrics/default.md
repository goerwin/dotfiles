# Rubric: default

Report what the author would likely act on:

- Bugs, broken edge cases, missing behavior, and regressions the change introduces.
- Unnecessary scope, duplicated logic, or departures from established patterns
  that materially harm correctness or maintenance.
- Workarounds that hide a problem: swallowed errors, sleeps/retries, broad
  overrides, unsafe casts.
- Missing regression coverage or repository-required release metadata.

Skip formatting, pre-existing issues, speculation, praise, and generated
snapshots. Recommend root-cause fixes. Severity: blocking or suggestion.
