# Plan: Consolidate Goerwin skills behind one dispatcher

## Objective

Replace the five independently installed Goerwin skills with one explicitly invoked `goerwin` skill. Keep each workflow's detailed instructions in a separate reference file, share review standards where useful, and preserve each workflow's safeguards and behavior.

Current skills:

- `goerwin-code-review`
- `goerwin-receiving-code-review`
- `goerwin-review-loop`
- `goerwin-architecture-review`
- `goerwin-handoff`

## Proposed structure

```text
src/.agents/skills/goerwin/
  SKILL.md
  agents/openai.yaml
  references/
    review-standards.md
    rubrics/default.md
    rubrics/adversarial.md
    workflows/
      code-review.md
      receiving-code-review.md
      review-loop.md
      architecture-review.md
      handoff.md
  scripts/
    review_pr.py
    receiving.py
    review_loop.py
    launch.py
  tests/
    test_review_pr.py
    test_receiving.py
    test_review_loop.py
```

The dispatcher should classify an explicit request and read only the relevant workflow reference. Route review, receiving feedback, review loop, architecture review, and handoff as distinct modes. Ask if the requested mode is unclear. References are workflow guides, not independently invokable skills.

Put shared code-review rules in `review-standards.md`: establish intent first, verify claims with evidence, fix root causes, reject test-only green changes and workarounds, preserve existing test intent when adapting tests, and mutation-test new production behavior. Keep mode-specific steps in their workflow references.

Keep the existing report IDs such as `goerwin-code-review` and `goerwin-architecture-review` where they are stored in report metadata. This preserves report history and filters even though the user-facing skill becomes `$goerwin`.

## Implementation steps

1. Create the umbrella skill and dispatcher. Preserve explicit invocation requirements and route each mode without inferring handoff or review-loop actions from ordinary review requests.
2. Move the five skill guides into `references/workflows/`. Extract shared review rules once. Retain default and adversarial rubrics as separate references.
3. Move each helper script and its tests under the umbrella folder. Update script-relative paths, imports, guide loading, rubric loading, and review-loop helper paths. Keep behavior unchanged apart from paths and dispatch.
4. Update all user-facing references and metadata: `README.md`, `agents/openai.yaml`, helper command examples, report skill IDs where appropriate, and `bin/install-skills.zsh`.
5. Handle old installed skill names safely. The installer currently copies skills into `.agents/skills` and creates Claude/Codex links, but does not remove obsolete entries. Retire only managed legacy entries, preserve customized or unrelated content, and verify the migration in a temporary `GOERWIN_SKILLS_HOME`.
6. Carry forward the current uncommitted review-guidance edits from the code-review rubrics and receiving-review guide into the shared standards and workflow references. Do not drop or duplicate those rules.

## Safeguards to preserve

- Handoff must remain explicitly requested, create a fresh visible interactive agent, and never relaunch after an uncertain launch.
- Review loop must keep its confirmation boundary, no-push behavior, waiting flow, and single final squash behavior.
- Receiving feedback must continue to require a user choice when feedback is not specified, preview GitHub replies before posting, and ask before commit, push, or reply.
- Code review must retain frozen-revision handling, existing-comment checks, read-only review behavior, and report completion requirements.
- Architecture review must remain report-only unless the user asks for fixes.

## Verification and acceptance

- Run the existing code-review, receiving-review, and review-loop test suites from their new locations. Add or adjust tests only for changed path or dispatch behavior.
- Verify each dispatcher mode loads its intended workflow and does not run a different mode when the request is ambiguous.
- Install to a temporary skills home and confirm only the umbrella skill is installed, old managed entries are retired safely, and unrelated files or links are preserved.
- Check all script and documentation references for old skill paths. Confirm legacy report IDs and existing review archives remain readable.
- Do not launch a handoff, post to GitHub, push, or commit as part of verification.

## Handoff note

Start by checking the working tree and preserving the four existing modified review-guidance files. Implement the structural migration in focused steps, then verify paths, install behavior, and existing tests before removing any legacy installation entries.
