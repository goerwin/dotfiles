## Rules

- **Git:** commit as needed, in small commits with short conventional subjects
  (`fix: keep cursors stable across pages`). Never squash or rewrite history
  unless asked. Never stash, reset, or discard work you didn't make.
- **Publishing:** ask before pushing or posting anything to GitHub (replies,
  comments, PR description edits). The request names the signed-in account
  (`gh api user --jq .login`) and where each item lands. Push only to the PR's
  branch, never the default branch.
- **GitHub text:** replies, comments, and PR descriptions sound like a person
  wrote them: casual, direct, brief, no hedging, no em dashes. No praise
  openers ("Good catch"), restating the comment, "I've updated X to Y"
  narration, or lists and headers in short replies. When the fix speaks for
  itself, "Fixed" or "Done" is the whole reply; add more only when it tells the
  reviewer something the fix doesn't.
- **Scope:** a PR URL must belong to the current checkout's repository; never
  clone.
