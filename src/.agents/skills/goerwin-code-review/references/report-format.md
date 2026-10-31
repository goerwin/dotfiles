# Saved review contract, version 1

The helper adds a flat YAML frontmatter mapping to the reviewer's Markdown body.
Values are JSON-encoded YAML values, so both scripts can read them without a
third-party YAML dependency. Consumers may use a standard safe YAML parser.

The metadata includes:

- schema_version: 1, kind: code_review, stable review_id, UTC created_at and
  completed_at.
- project, canonical repository identity, source_path/source_common_dir,
  target_key, title, PR URL/number when applicable, head/base refs, full
  head/base/merge-base SHAs, and selected PR vs local revision.
- Requested harness, model, effort, preset_id, and selected GitHub username.
- finding_ids, matching the body headings F1, F2, etc.

The body contains assessment, findings, checks and verification limits.
No-findings reports explicitly state "No actionable findings."

Every actionable finding is headed "### F1: Short title" and includes its
path/new-side line, blocking vs suggestion, evidence and a sound root-cause fix.
A portable source reference is review_id:F1. Filenames are for browsing and must
not be parsed to establish identity or revision.

Completion finalizes the report once and records its hash in the run metadata.
Receiving never modifies the original. A receiving receipt has kind: receiving,
its own receipt_id, repository/branch and before/after HEAD, source review_ids,
and an outcomes array of sources/outcome groups. Its Markdown body contains
evidence, decisions, questions and checks. Receipts live in .receiving; imported
pasted inputs live in .inputs, and run state lives in .runs.

Receiving can group semantically duplicate findings after validating them.
Preserve every source reference. A group has one applied, pushed_back, or waiting
outcome. Do not merge conflicting recommendations merely because their locations
overlap. Prior applied/pushed_back references are inactive; waiting ones remain
eligible for a later pass.
