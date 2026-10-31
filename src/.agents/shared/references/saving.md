# Saving a review

Write the review body to a temporary Markdown file: a short assessment, then
one section per finding, then checks and limits.

~~~md
### F1: Short title

`path/to/file.ts:42-48` · high

Failure scenario or maintenance cost, then the root-cause fix.
~~~

IDs are unique (F1, F2, …). Then save it with your own harness, model, and effort:

~~~sh
goerwin-review save --body /tmp/review.md --skill SKILL_NAME \
  --harness claude --model MODEL_ID --effort EFFORT \
  [--pr URL | --head REF --base REF | --scope PATH] -C /reviewed/checkout
~~~

Use `--pr` or `--head/--base` for change reviews and `--scope` for a snapshot of
the current HEAD. The command records the commits and project and prints the
saved path; link it in your reply. `goerwin-receiving-code-review` can then act
on it.
