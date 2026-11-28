## Probes

Every reviewer uses these probes with any rubric:

- Public surface: every accepted prop, option, and type member works in every
  branch; otherwise remove it from the type.
- Precedence: component default < parent context < explicit consumer value,
  including `false`. State set on a container (disabled, invalid, size)
  reaches every composed part, including hidden or native ones, and a
  consumer's class or style still beats the component's own.
- Composition: nest an instance inside itself, put a slot inside a wrapper,
  swap child order, and try unexpected or primitive children (string, number).
  Queries, selectors, and handlers stop at the nearest instance; inherited
  styles and context don't leak in from ancestors or out to unrelated
  descendants.
- Interaction: decide who owns each press when controls nest, content is
  portaled, or input is a drag, long press, keyboard, or programmatic click.
  One action fires each handler once, and hover-only behavior is limited to
  devices that hover.
- Inputs: try `0`, `''`, empty collections, out-of-bounds values, intrinsic
  sizing keywords, and very small and large containers.
- Lifecycle: mount and unmount mid-action; repeat or reorder calls, including
  several in one handler; check cleanup, animations that never end, and
  supported framework/runtime versions.
- Environment: check SSR, hydration, RTL, reduced motion, portals, touch,
  keyboard, and pointer. A reduced-motion path still fires the events the
  normal path waits on, and styling reaches portaled content without relying
  on inheritance.
- Accessibility: names and descriptions reach the focusable element; focus
  moves somewhere sensible on close, and closing content can't be operated.
  Text and icons meet contrast.
- Paired values: when one value of a pair changes (foreground and background,
  a token and its fallback), the other follows; every referenced token,
  constant, or config key exists.
- CI: workflow triggers are limited to trusted actors, and jobs get only the
  permissions they need.
- Promises: every claim in docs and types holds in combination, not just in
  one case at a time.
