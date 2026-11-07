# Rubric: default

Report what the author would likely act on:

- Bugs, broken edge cases, missing behavior, and regressions the change introduces.
- Unnecessary scope, duplicated logic, or departures from established patterns
  that materially harm correctness or maintenance.
- Workarounds that hide the cause or change tests only to force a pass.
- Missing regression coverage or repository-required release metadata.

Check the user's or PR's intent before judging behavior. Preserve existing
tests' purpose when adapting them; add tests only for uncovered behavior.
Mutation-test new production code by removing or reversing each new behavior
and confirming relevant tests fail.

Skip formatting, pre-existing issues, speculation, praise, and generated
snapshots. Recommend root-cause fixes. Severity: blocking or suggestion.
