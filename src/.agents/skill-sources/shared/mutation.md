## Mutation check

Inject plausible bugs (mutants) into the changed code and see which tests
fail. A mutant that survives is behavior no test protects; a test that kills
no mutant is likely noise.

### Scope

Mutate only changed, non-test lines since the [base](#base). Run the tests the
change adds or edits, plus the existing tests for the touched modules.

### Setup

- Run the scoped tests twice on unmodified code. They must pass both times; if
  they fail or flake, stop and report that instead.
- Save `git status` and `git diff` output, and copy each file to
  `/tmp/mutation/` before you first mutate it. Never commit, stash, or reset
  while mutants are applied.
- Don't run this while another agent is editing the same checkout.

### Mutants

Pick 5 to 20 mutants on the changed lines, each a bug the author could
realistically write, applied one at a time:

- **Remove:** delete the new branch, call, side effect, or validation, or
  return early.
- **Reverse:** negate a condition, swap branches, flip a default.
- **Boundaries:** `<` to `<=`, off by one, drop an empty, null, or error case.
- **Values:** return a constant, drop a field, swap arguments, swallow an error
  or skip an `await`.

Mutants must compile and type-check. Skip equivalent mutants (no observable
difference) and mutants in logging, types, or comments.

If the project already configures a mutation tool (Stryker, mutmut,
cargo-mutants, PIT), you may use it limited to the changed files or lines.
Don't install one without asking.

### Run

For each mutant: apply it, run the scoped tests, record **killed** (and by
which tests) or **survived**, then restore the file from `/tmp/mutation/`. Run
the full suite on survivors before reporting them, since existing coverage
elsewhere counts. When done, confirm `git status` and `git diff` match the
saved output exactly.

### Judge

- **Survivor:** confirm the behavior is observable to a caller; if not, the
  mutant is equivalent, so drop it. Otherwise report the missing assertion.
- **Test that kills nothing:** likely bloat. Check whether it covers behavior
  outside the diff before you call it bloat.
- **Test whose kills another test already makes:** candidate to merge into
  that test.
- **Kills only through mock call counts, snapshots, or private state:** the
  test is coupled to implementation details, not behavior.

### Tables

After the findings, the report adds:

~~~md
## Mutants

Score: 9/11 killed (2 equivalent skipped)

| # | Location | Mutation | Result | Killed by |
| --- | --- | --- | --- | --- |
| M1 | `src/cart.ts:42` | `>` to `>=` | survived | |
| M2 | `src/cart.ts:57` | drop discount call | killed | `applies discount` |

## Tests

| Test | Kills | Unique kills |
| --- | --- | --- |
| `applies discount` | M2, M5 | M2 |
| `renders cart` | none | none |
~~~

To fix, add assertions that kill survivors and remove or merge bloat tests,
then rerun the affected mutants to verify.
