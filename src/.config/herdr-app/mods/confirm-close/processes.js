export function targetTab(spaces, requested) {
  if (requested === undefined) {
    const space = spaces.find((item) => item.active);
    const tab = space?.tabs.find((item) => item.active);
    return tab ? { space, tab } : null;
  }
  if (typeof requested !== 'string' || !requested) return null;
  for (const space of spaces) {
    const tab = space.tabs.find((item) => item.id === requested);
    if (tab) return { space, tab };
  }
  return null;
}

export function tabTerminals(panes, terminals) {
  const selected = new Map();
  for (const pane of panes) {
    if (!pane.terminal) continue;
    selected.set(
      pane.terminal,
      terminals.find((item) => item.address === pane.terminal) ?? {
        address: pane.terminal,
        program: pane.program,
      },
    );
  }
  // Core terminals started by an agent can outnumber its visible panes.
  for (;;) {
    let added = false;
    for (const terminal of terminals) {
      if (!terminal.parent || selected.has(terminal.address)) continue;
      const prefix = terminal.address.slice(
        0,
        terminal.address.lastIndexOf('/') + 1,
      );
      const parent = terminal.parent.includes('/')
        ? terminal.parent
        : prefix + terminal.parent;
      if (!selected.has(parent)) continue;
      selected.set(terminal.address, terminal);
      added = true;
    }
    if (!added) return [...selected.values()];
  }
}

export function runningWork(terminals, listing) {
  const processes = new Map();
  for (const line of listing?.split('\n') ?? []) {
    const match = line.match(/^\s*(\d+)\s+(\d+)\s+(\S+)\s+(.+)$/);
    if (!match) continue;
    processes.set(Number(match[1]), {
      pid: Number(match[1]),
      parent: Number(match[2]),
      state: match[3][0],
      name: match[4].trim().split('/').pop(),
    });
  }

  return terminals.flatMap((terminal) => {
    if (terminal.state === 'finished') return [];
    const name = terminal.program?.name || terminal.name || terminal.address;
    if (terminal.state !== 'live')
      return [`${name}: process details unavailable`];
    if (terminal.program?.shell !== true) return [name];

    const root = processes.get(terminal.pid);
    if (!root) return [`${name}: process details unavailable`];
    const descendants = new Set([root.pid]);
    for (;;) {
      const before = descendants.size;
      for (const process of processes.values()) {
        if (descendants.has(process.parent)) descendants.add(process.pid);
      }
      if (descendants.size === before) break;
    }
    const children = [...descendants]
      .filter((pid) => pid !== root.pid)
      .map((pid) => processes.get(pid))
      .filter((process) => !['Z', 'X'].includes(process.state));
    if (children.length) {
      return [
        `${name}: ${[...new Set(children.map((process) => process.name))].join(', ')}`,
      ];
    }
    // An idle shell sleeps at its prompt. An active/stopped shell may itself
    // be executing a builtin even when it has no external child process.
    return ['S', 'I', 'Z', 'X'].includes(root.state)
      ? []
      : [`${name}: active or stopped shell`];
  });
}
