// TODO: Track native confirmation for closing tabs/panes with running work:
// https://github.com/herdrdev/herdr-app/issues/35

import { h_flex, v_flex } from 'gpui-base';
import { div, View } from 'gpui-kit';
import {
  closeOverlay,
  exec,
  notify,
  openOverlay,
  panes,
  props,
  run,
  spaces,
  terminals,
  theme,
} from 'herdr';
import { runningWork, tabTerminals, targetTab } from './processes.js';

export default class ConfirmClose extends View {
  init(_props, cx) {
    this.phase = 'checking';
    this.work = [];
    this.cancelled = false;
    this.handle = cx.focus_handle();
    this.overlay = props()?.overlay;
    if (!this.overlay) return; // `herdr-app check` must never close a tab.

    const confirmation = props()?.confirmation;
    if (confirmation) {
      this.parent = confirmation.parent;
      this.target = confirmation.target;
      this.work = confirmation.work;
      if (!this.targetExists()) {
        this.cancel();
        return;
      }
      this.phase = 'confirm';
      this.handle.focus();
      return;
    }

    const target = targetTab(spaces(), props()?.tab);
    if (!target) {
      notify({
        title: 'Close tab',
        body: 'No matching tab is open.',
        level: 'warning',
      });
      this.cancel();
      return;
    }
    this.target = {
      id: target.tab.id,
      name: target.tab.name,
      space: target.space.id,
      spaceName: target.space.name,
      machine: target.space.machine,
      last: target.space.tabs.length === 1,
    };
    const records = tabTerminals(
      panes().filter((pane) => pane.tab === this.target.id),
      terminals(),
    );
    cx.spawn(async (cx) => {
      let listing = null;
      if (
        records.some(
          (terminal) =>
            terminal.state === 'live' && terminal.program?.shell === true,
        )
      ) {
        try {
          const result = await exec('ps', ['-axo', 'pid=,ppid=,stat=,comm='], {
            on: this.target.machine,
          });
          if (result.code === 0) listing = result.stdout;
        } catch {
          // Missing/unsupported process inspection requires confirmation.
        }
      }
      if (this.cancelled) return;
      cx.notify(); // Also stop a task belonging to a closed/reloaded view.
      if (!this.targetExists()) {
        this.cancel();
        return;
      }
      const currentSpace = spaces().find(
        (space) => space.id === this.target.space,
      );
      const currentTab = currentSpace.tabs.find(
        (tab) => tab.id === this.target.id,
      );
      const currentPanes = panes().filter(
        (pane) => pane.tab === this.target.id,
      );
      this.target.last = currentSpace.tabs.length === 1;
      this.work =
        currentPanes.length === currentTab.panes
          ? runningWork(tabTerminals(currentPanes, terminals()), listing)
          : ['Terminal information is incomplete'];
      if (!this.work.length) {
        closeOverlay(this.overlay);
        // Keep Herdr's existing last-tab / space-close confirmation.
        run('tab.close', { id: this.target.id });
        return;
      }
      // Only mount a dialog after inspection; the shortcut's tiny, frameless
      // window renders nothing and never takes focus or dims the workspace.
      this.dialog = openOverlay({
        mod: 'confirm-close',
        props: {
          confirmation: {
            target: this.target,
            work: this.work,
            parent: this.overlay,
          },
        },
        kind: 'dialog',
        width: 480,
        height: 300,
      });
    });
  }

  targetExists() {
    return spaces().some(
      (space) =>
        space.id === this.target?.space &&
        space.tabs.some((tab) => tab.id === this.target.id),
    );
  }

  cancel() {
    this.cancelled = true;
    if (this.overlay) closeOverlay(this.overlay);
  }

  close() {
    this.cancelled = true;
    // Keep the shortcut's toggle and the visible dialog in sync.
    const linked = this.dialog ?? this.parent;
    if (linked) closeOverlay(linked);
  }

  confirm() {
    if (this.cancelled || this.phase !== 'confirm') return;
    const exists = this.targetExists();
    const space = spaces().find((item) => item.id === this.target?.space);
    const confirmed = space?.tabs.length !== 1 || this.target.last;
    this.cancel();
    if (exists) run('tab.close', { id: this.target.id, confirmed });
  }

  render() {
    if (this.phase !== 'confirm') return div();
    const t = theme();
    const button = (id, text, action, primary = false) =>
      div()
        .id(id)
        .px(14)
        .py(7)
        .rounded(6)
        .cursor_pointer()
        .bg(primary ? t.solid : t.raised)
        .text_color(primary ? t.solid_foreground : t.foreground)
        .hover((style) => style.opacity(0.85))
        .on_click(action)
        .child(text);

    return v_flex()
      .id('confirm-close')
      .size_full()
      .p(18)
      .gap(12)
      .bg(t.popover)
      .text_color(t.foreground)
      .text_size(13)
      .track_focus(this.handle)
      .on_key_down((event, cx) => {
        if (event.key === 'escape') this.cancel();
        else if (event.key === 'enter') this.confirm();
        else return;
        cx.stop_propagation();
      })
      .child(div().text_size(16).font_semibold().child('Close tab?'))
      .child(
        v_flex()
          .flex_1()
          .min_h(0)
          .gap(6)
          .overflow_y_scrollbar()
          .child(
            `Closing “${this.target.name}” in “${this.target.spaceName}” will stop running work:`,
          )
          .children(
            this.work.map((work) =>
              div().text_color(t.muted).child(`• ${work}`),
            ),
          )
          .when(this.target.last, (element) =>
            element.child(
              div()
                .mt(6)
                .text_color(t.muted)
                .child('This is the last tab, so its space will also close.'),
            ),
          ),
      )
      .child(
        h_flex()
          .justify_end()
          .gap(8)
          .child(button('cancel-close', 'Cancel', () => this.cancel()))
          .child(
            button(
              'confirm-tab-close',
              'Close tab',
              () => this.confirm(),
              true,
            ),
          ),
      );
  }
}
