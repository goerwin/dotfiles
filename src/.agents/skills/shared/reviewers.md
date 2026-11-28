## Reviewers

Reviewers are models from different providers, each reviewing independently.

- Pick them: by default the latest frontier model of two or three providers at
  high effort. Use the models the user names; one named model is a single
  reviewer.
- Show the number of reviewers and, for each, the provider, exact model
  version, effort, and where it runs (internal subagent or separate agent),
  plus the rubric and any round limit. Wait for confirmation.

Give each reviewer the request, intent, context, and review base, plus the
[Standards](#standards), [What to report](#what-to-report),
[Findings format](#findings-format), [Probes](#probes), and the rubric copied
into its prompt. Tell each to read the repository's `AGENTS.md`,
`.github/copilot-instructions.md`, `.github/instructions/*`, and any docs or
skills they reference; read these yourself too. When that guidance contradicts
the code's established patterns, follow the code and note the conflict.
Leave out the implementer's reasoning for its choices, so each judges the work
fresh. Reviewers are read-only and don't start other agents. Ask each for
findings in the findings format, a score out of 10, and any questions only the
user can answer.

Use the harness's own subagents when they support the model. Otherwise start
the reviewer as a separate agent, the way your agent orchestrator documents.
Write its prompt to a file (e.g. `/tmp/reviewers/REVIEWER-prompt.md`) and have
it write its findings to another.

Wait without sleeping; a timeout is a check-in, not a failure. If a reviewer
stops without its findings file, read its output before deciding anything, and
never start a duplicate. Close separate agents once you have their results.

While reviewers run:

- Don't wait idle. Verify each result against the code as it arrives.
- Don't edit files while a reviewer is still reviewing the same checkout.
- If the user marks a reviewer as non-blocking, don't wait for it. Treat a late
  result as feedback and don't record its score.

Merge duplicate findings by their real underlying issue, and drop claims the
code doesn't support. Record the scores in the report:

```markdown
## Reviewers

| Reviewer | Round 1 | Round 2 |
| --- | --- | --- |
| Model A | 7/10 | 9/10 |
| Model B | 8/10 | 10/10 |
```

If a reviewer gives no score, write `no score`; never invent one. The table
goes in the reply and the report, never on GitHub.
