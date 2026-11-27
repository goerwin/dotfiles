## Rubrics

Use a rubric only when the user or this skill asks for it.

**Adversarial:** assume the change is broken and try to break it. Probe invalid
inputs, boundaries, unusual option combinations, repeated or out-of-order
actions, races, partial failures, and cleanup; judge APIs as a consumer and
code as the next maintainer. Each finding needs a concrete failure path or
maintenance cost, plus a simpler alternative. Severity: critical, high,
medium, or low.

**Design:** judge the approach, not the lines. Would you solve the goal this
way from scratch? Does the change solve the general problem or only the
reported case? Flag special cases bolted on instead of fixing the underlying
model, logic spread across places one should own, states or flows the goal
implies but the change misses, and simpler designs that remove code. Each
finding needs the concrete gap and the alternative.
