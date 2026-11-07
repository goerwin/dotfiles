# Findings

Use this format in chat and in saved reports: the source and reviewed SHAs, a
short assessment, then one section per finding.

~~~md
### F1: Short title

`path/to/file.ts:42-48` (new side) · severity

Evidence or failure scenario, then a brief root-cause fix.
~~~

IDs are unique (F1, F2, …). Severity uses the rubric's or mode's scale. With no
findings, write "No actionable findings." End with the checks you ran and any
verification limits. Don't pad.
