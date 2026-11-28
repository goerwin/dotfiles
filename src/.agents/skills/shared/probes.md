## Probes

Every reviewer uses these probes with any rubric:

- Public surface: every accepted prop, option, and type member works in every
  branch; otherwise remove it from the type.
- Precedence: component default < parent context < explicit consumer value,
  including `false`.
- Composition: nest an instance inside itself, put a slot inside a wrapper,
  swap child order, and try unexpected or primitive children (string, number).
- Inputs: try `0`, `''`, empty collections, out-of-bounds values, and very small
  and large containers.
- Lifecycle: mount and unmount mid-action; repeat or reorder calls; check
  cleanup and supported framework/runtime versions.
- Environment: check SSR, hydration, RTL, reduced motion, portals, touch,
  keyboard, and pointer.
- Accessibility: names and descriptions reach the focusable element; focus
  moves somewhere sensible on close.
- Promises: every claim in docs and types holds in combination, not just in
  one case at a time.
