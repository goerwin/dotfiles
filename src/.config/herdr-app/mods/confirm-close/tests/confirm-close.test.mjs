import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const mainSource = await readFile(
  new URL('../main.js', import.meta.url),
  'utf8',
);
const policySource = await readFile(
  new URL('../processes.js', import.meta.url),
  'utf8',
);
const policy = await import(
  `data:text/javascript;base64,${Buffer.from(policySource).toString('base64')}`
);
const idleProcesses = '101 1 S /bin/zsh\n999 1 S unrelated-server\n';
const shell = {
  address: 'a1',
  pid: 101,
  state: 'live',
  program: { name: 'zsh', shell: true },
};
const agent = {
  ...shell,
  program: { name: 'Codex', shell: false, agent: true },
  status: 'idle',
};

test('selects the active tab, or a validated explicit tab in another space', () => {
  const spaces = [
    { id: 's1', active: false, tabs: [{ id: 't1', active: true }] },
    { id: 's2', active: true, tabs: [{ id: 't2', active: true }] },
  ];
  assert.equal(policy.targetTab(spaces).tab.id, 't2');
  assert.equal(policy.targetTab(spaces, 't1').space.id, 's1');
  for (const invalid of [null, 1, '', 'missing']) {
    assert.equal(policy.targetTab(spaces, invalid), null);
  }
  assert.equal(policy.targetTab([]), null);
});

test('collects only this tab and its transitive child terminals', () => {
  const records = policy.tabTerminals(
    [{ terminal: 'a1' }],
    [
      shell,
      { address: 'grandchild', parent: 'child', state: 'live' },
      { address: 'child', parent: 'a1', state: 'live' },
      { address: 'unrelated', state: 'live' },
    ],
  );
  assert.deepEqual(
    new Set(records.map((item) => item.address)),
    new Set(['a1', 'child', 'grandchild']),
  );
  assert.equal(
    policy.tabTerminals([{ terminal: 'missing' }], [])[0].address,
    'missing',
  );
  assert.deepEqual(
    policy.tabTerminals([{ terminal: null, mod: 'viewer' }], []),
    [],
  );
});

test('resolves remote child addresses on the same machine', () => {
  const records = policy.tabTerminals(
    [{ terminal: 'vps/a1' }],
    [
      { address: 'vps/a1', state: 'live' },
      { address: 'vps/a2', parent: 'a1', state: 'live' },
      { address: 'other/a3', parent: 'a1', state: 'live' },
    ],
  );
  assert.deepEqual(
    records.map((item) => item.address),
    ['vps/a1', 'vps/a2'],
  );
});

test('idle shells and finished terminals need no custom confirmation', () => {
  assert.deepEqual(policy.runningWork([shell], idleProcesses), []);
  assert.deepEqual(
    policy.runningWork([{ ...agent, state: 'finished' }], null),
    [],
  );
});

test('live agents remain protected while waiting for input or reporting done', () => {
  for (const status of ['working', 'blocked', 'idle', 'done']) {
    assert.deepEqual(policy.runningWork([{ ...agent, status }], null), [
      'Codex',
    ]);
  }
});

test('background and nested jobs are protected; unrelated and zombie jobs are ignored', () => {
  const listing = `${idleProcesses}202 101 S /usr/bin/node\n203 202 S /bin/sleep\n204 101 Z defunct\n`;
  assert.deepEqual(policy.runningWork([shell], listing), ['zsh: node, sleep']);
  assert.deepEqual(
    policy.runningWork([shell], `${idleProcesses}204 101 Z defunct\n`),
    [],
  );
});

test('unknown state, unsupported inspection, and active shell builtins require confirmation', () => {
  assert.ok(policy.runningWork([shell], null).length);
  assert.ok(policy.runningWork([shell], 'invalid process data').length);
  assert.ok(policy.runningWork([{ address: 'missing' }], idleProcesses).length);
  assert.ok(policy.runningWork([shell], '101 1 R /bin/zsh\n').length);
});

function element() {
  const proxy = new Proxy(
    {},
    {
      get:
        () =>
        (...args) => {
          if (
            typeof args[0] === 'boolean' &&
            args[0] &&
            typeof args[1] === 'function'
          )
            return args[1](proxy);
          return proxy;
        },
    },
  );
  return proxy;
}

async function harness({
  terminal = agent,
  props = { overlay: 'dialog' },
  execute,
} = {}) {
  const state = {
    spaces: [
      {
        id: 's1',
        name: 'Project',
        active: true,
        machine: null,
        tabs: [
          { id: 't1', name: 'Work', active: true, panes: 1 },
          { id: 't2', name: 'Other', active: false, panes: 1 },
        ],
      },
    ],
    panes: [{ pane: 'p1', tab: 't1', terminal: 'a1' }],
    terminals: [terminal],
  };
  const calls = {
    run: [],
    close: [],
    exec: [],
    notifications: [],
    open: [],
    focus: [],
  };
  const instances = new Map();
  let dialog;
  let currentProps = props;
  const normalize = (value) => JSON.parse(JSON.stringify(value));
  const api = {
    props: () => currentProps,
    spaces: () => state.spaces,
    panes: () => state.panes,
    terminals: () => state.terminals,
    theme: () => ({}),
    closeOverlay: (id) => {
      const instance = instances.get(id);
      if (!instance) return;
      instances.delete(id);
      calls.close.push(id);
      instance.close();
    },
    openOverlay: (spec) => {
      calls.open.push(normalize(spec));
      dialog = mount({ ...spec.props, overlay: 'confirmation-dialog' });
      return 'confirmation-dialog';
    },
    run: (name, args) => calls.run.push([name, normalize(args)]),
    notify: (value) => calls.notifications.push(normalize(value)),
    exec: async (...args) => {
      calls.exec.push(normalize(args));
      return execute ? execute(...args) : { code: 0, stdout: idleProcesses };
    },
  };
  const context = vm.createContext({ Error });
  const exports = {
    herdr: api,
    'gpui-kit': { View: class {}, div: element },
    'gpui-base': { h_flex: element, v_flex: element },
  };
  const modules = Object.fromEntries(
    Object.entries(exports).map(([name, values]) => [
      name,
      new vm.SyntheticModule(
        Object.keys(values),
        function () {
          for (const [key, value] of Object.entries(values))
            this.setExport(key, value);
        },
        { context },
      ),
    ]),
  );
  modules['./processes.js'] = new vm.SourceTextModule(policySource, {
    context,
  });
  const main = new vm.SourceTextModule(mainSource, { context });
  await main.link((name) => modules[name]);
  await main.evaluate();
  const pending = [];
  function mount(modProps) {
    const instance = new main.namespace.default();
    instances.set(modProps.overlay, instance);
    const cx = {
      notify() {},
      focus_handle: () => ({ focus: () => calls.focus.push(modProps.overlay) }),
      spawn(task) {
        pending.push(task(cx));
      },
    };
    const previousProps = currentProps;
    currentProps = modProps;
    instance.init({}, cx);
    instance.render();
    currentProps = previousProps;
    return instance;
  }
  const instance = mount(props);
  return {
    instance,
    state,
    calls,
    get dialog() {
      return dialog;
    },
    drain: () => Promise.all(pending),
  };
}

test('checking the mod without overlay props never inspects or closes anything', async () => {
  const h = await harness({ props: {} });
  await h.drain();
  assert.deepEqual(h.calls, {
    run: [],
    close: [],
    exec: [],
    notifications: [],
    open: [],
    focus: [],
  });
});

test('busy tab needs an explicit confirmation, which still targets its captured ID', async () => {
  const h = await harness();
  await h.drain();
  assert.equal(h.dialog.phase, 'confirm');
  assert.equal(h.calls.run.length, 0);
  h.state.spaces[0].tabs[0].active = false;
  h.state.spaces[0].tabs[1].active = true;
  h.dialog.confirm();
  h.dialog.confirm();
  assert.deepEqual(h.calls.run, [['tab.close', { id: 't1', confirmed: true }]]);
  assert.deepEqual(h.calls.close, ['confirmation-dialog', 'dialog']);
});

test('idle shell closes only its captured tab and preserves native space confirmation', async () => {
  const h = await harness({ terminal: shell });
  await h.drain();
  assert.deepEqual(h.calls.run, [['tab.close', { id: 't1' }]]);
  assert.deepEqual(h.calls.open, []);
  assert.deepEqual(h.calls.focus, []);
  assert.equal(h.calls.exec[0][0], 'ps');
  assert.deepEqual(h.calls.exec[0][2], { on: null });
});

test('inspection failure leaves the tab running and asks instead', async () => {
  const h = await harness({
    terminal: shell,
    execute: async () => {
      throw new Error('unavailable');
    },
  });
  await h.drain();
  assert.equal(h.dialog.phase, 'confirm');
  assert.equal(h.calls.run.length, 0);
});

test('Cancel and Enter during an unfinished inspection cannot close the tab', async () => {
  let finish;
  const h = await harness({
    terminal: shell,
    execute: () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  });
  h.instance.confirm();
  assert.equal(h.calls.run.length, 0);
  h.instance.cancel();
  finish({ code: 0, stdout: idleProcesses });
  await h.drain();
  assert.deepEqual(h.calls.run, []);
});

test('a disappeared target never redirects a close to the new active tab', async () => {
  const h = await harness();
  await h.drain();
  h.state.spaces[0].tabs.shift();
  h.dialog.confirm();
  assert.deepEqual(h.calls.run, []);
  assert.deepEqual(h.calls.close, ['confirmation-dialog', 'dialog']);
});

test('a newly added running pane is rechecked after process inspection', async () => {
  let finish;
  const h = await harness({
    terminal: shell,
    execute: () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  });
  h.state.panes.push({ pane: 'p2', tab: 't1', terminal: 'a2' });
  h.state.terminals.push({ ...agent, address: 'a2' });
  h.state.spaces[0].tabs[0].panes = 2;
  finish({ code: 0, stdout: idleProcesses });
  await h.drain();
  assert.equal(h.dialog.phase, 'confirm');
  assert.deepEqual(h.calls.run, []);
});

test('incomplete pane data requires confirmation', async () => {
  let finish;
  const h = await harness({
    terminal: shell,
    execute: () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  });
  h.state.spaces[0].tabs[0].panes = 2;
  finish({ code: 0, stdout: idleProcesses });
  await h.drain();
  assert.equal(h.dialog.phase, 'confirm');
  assert.deepEqual(h.calls.run, []);
});

test('if another tab disappears after the prompt, native last-tab confirmation stays enabled', async () => {
  const h = await harness();
  await h.drain();
  h.state.spaces[0].tabs.pop();
  h.dialog.confirm();
  assert.deepEqual(h.calls.run, [
    ['tab.close', { id: 't1', confirmed: false }],
  ]);
});

test('inspection stays invisible and leaves focus alone until work is found', async () => {
  let finish;
  const h = await harness({
    terminal: shell,
    execute: () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  });
  assert.deepEqual(h.calls.open, []);
  assert.deepEqual(h.calls.focus, []);
  assert.equal(h.dialog, undefined);
  // Selection changes during the invisible check cannot change the target.
  h.state.spaces[0].tabs[0].active = false;
  h.state.spaces[0].tabs[1].active = true;
  finish({ code: 0, stdout: `${idleProcesses}202 101 S node\n` });
  await h.drain();
  assert.equal(h.calls.open.length, 1);
  assert.equal(h.calls.open[0].kind, 'dialog');
  assert.equal(h.calls.open[0].props.confirmation.target.id, 't1');
  assert.deepEqual(h.calls.focus, ['confirmation-dialog']);
  h.dialog.confirm();
  assert.deepEqual(h.calls.run, [['tab.close', { id: 't1', confirmed: true }]]);
});

test('toggling the shortcut while the dialog is open cancels both copies', async () => {
  const h = await harness();
  await h.drain();
  h.instance.cancel();
  h.dialog.confirm();
  assert.deepEqual(h.calls.run, []);
  assert.deepEqual(h.calls.close, ['dialog', 'confirmation-dialog']);
});

test('dismissing the dialog also removes its invisible shortcut copy', async () => {
  const h = await harness();
  await h.drain();
  h.dialog.cancel();
  assert.equal(h.instance.cancelled, true);
  assert.deepEqual(h.calls.run, []);
  assert.deepEqual(h.calls.close, ['confirmation-dialog', 'dialog']);
});
