## Base

Fetch, then compare the branch with its PR's base
(`gh pr view --json url,baseRefName`), or with the remote default branch when
there is no PR. Diff from the merge base
(`git diff $(git merge-base origin/BASE HEAD)`) so uncommitted work is
included.
