import { div, View } from 'gpui-kit';
import { closeOverlay, focused, props, run, spaces } from 'herdr';

export default class MoveTab extends View {
  init(_props, cx) {
    const { overlay, delta } = props() ?? {};
    if (!overlay) return;

    const context = focused();
    const space = spaces().find((space) => space.id === context?.space);
    const index = space?.tabs.findIndex((tab) => tab.id === context?.tab) ?? -1;
    const target = index + delta;

    cx.spawn(async () => {
      try {
        if (
          (delta === -1 || delta === 1) &&
          index >= 0 &&
          target >= 0 &&
          target < space.tabs.length
        ) {
          run('tab.move', { id: context.tab, index: target + 1 });
        }
      } finally {
        closeOverlay(overlay);
      }
    });
  }

  render() {
    return div();
  }
}
