# Addressing findings

For each active finding, establish the expected behavior, then verify the claim
against current code, callers, and tests; revalidate stale reviews.
Previously applied or pushed-back findings are inactive; waiting ones come back.

Group duplicates by their real underlying issue, keeping every `review_id:F1`
source; matching file and line alone isn't a duplicate. Give each active source
exactly one outcome:

- **applied**: correct and a concrete improvement. Make a focused root-cause
  fix using existing patterns. An issue already fixed in current code counts,
  with that evidence.
- **pushed_back**: incorrect, speculative, out of scope, preference without
  benefit, a workaround, a test-only change that forces a pass, or a change of
  intent. Explain with evidence; suggest follow-up for valid out-of-scope ideas.
- **waiting**: needs facts only the user or reviewer has. Ask a concrete question.

Earlier approaches on the branch aren't constraints for new behavior. Reproduce
bugs and run focused checks when practical; preserve unrelated edits.

Write the outcomes as a JSON array; `waiting` outcomes also need a `question`:

~~~json
[{"sources": ["REVIEW_ID:F1", "OTHER_ID:F2"], "outcome": "applied",
  "explanation": "Preserved the cursor when loading the next page.",
  "evidence": "Both callers reuse that cursor; the regression now passes.",
  "checks": ["Focused pagination regression passed"]}]
~~~
