## Council

Two or three delegates review or give feedback, usually on code but also on
plans or designs.

### Before starting

- Make sure you have the intent, goal, and context. Ask for anything missing.
- Fix known issues and run relevant checks, so the council reviews the current
  implementation. Don't defer known fixes until reviews return.
- Pick the delegates: each a model from a different provider, by default the
  latest frontier model of each at high effort. Use the members the user
  names; one named model is a council of one.
- Show the number of delegates and, for each, the provider, exact model
  version, effort, and where it runs (internal subagent or separate agent),
  plus the rubric and round limit. Wait for confirmation.

### Running delegates

Give each delegate the request, intent, context, and review base, plus the
[Standards](#standards), [What to report](#what-to-report),
[Findings format](#findings-format), and the rubric copied into its prompt.
Leave out the implementer's reasoning for its choices, so each judges the work
fresh. Delegates are read-only and don't start other agents. For code
reviews, ask each for findings in the findings format, a score out of 10, and
any questions only the user can answer.

Use the harness's own subagents when they support the model. Otherwise start
the delegate as a separate agent, the way your agent orchestrator documents.
Write its prompt to a file (e.g. `/tmp/council/DELEGATE-prompt.md`) and have it
write its findings to another.

Wait without sleeping; a timeout is a check-in, not a failure. If a delegate
stops without its findings file, read its output before deciding anything, and
never start a duplicate. Close separate agents once you have their results.

While delegates run:

- Don't wait idle. Check each result against the code as it arrives and decide
  what to fix while the others run.
- Don't edit files while a delegate is still reviewing the same checkout.
- If the user marks a delegate as non-blocking, don't wait for it. Treat a late
  result as feedback and don't record its score.

### Rounds

Each full review pass is one round; a fresh review after fixes starts a new
one. Apply only the recommendations that meet the
[feedback bar](#standards), then request a fresh review. Repeat until all
delegates are satisfied, up to 5 rounds unless the user sets another limit. If
findings remain at the limit, stop and list them. Don't let repeated reviews
cause scope creep.

Answer delegate questions from code, docs, and history when you can. Ask the
user the rest in one batch per round, and keep fixing unrelated findings while
you wait. A finding that would change the approach or the intent is a
question, not a fix.

### Scores

Summarize the useful findings, disagreements, and what was applied or pushed
back, and save one report for the whole run with this table:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Model A | 7/10 | 9/10 |
| Model B | 8/10 | 10/10 |
```

If a delegate gives no score, write `no score`; never invent one. The table
goes in the reply and the report, never on GitHub.
