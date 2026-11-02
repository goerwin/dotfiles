import { div, View } from 'gpui-kit';
import { closeOverlay, exec, notify, props, spaces } from 'herdr';

export default class OpenCursor extends View {
  init(_props, cx) {
    // Only run when opened by the shortcut, not during `herdr-app check`.
    const overlay = props()?.overlay;
    if (!overlay) return;

    // Capture the selected space before an asynchronous task can change selection.
    const folder = spaces().find((space) => space.active)?.folder;
    cx.spawn(async () => {
      try {
        if (!folder) throw new Error('No selected space folder is available.');
        const result = await exec('/usr/bin/open', ['-a', 'Cursor', folder]);
        if (result.code !== 0) {
          throw new Error(
            result.stderr.trim() || `open exited with code ${result.code}`,
          );
        }
      } catch (error) {
        notify({
          title: 'Could not open Cursor',
          body: error instanceof Error ? error.message : String(error),
          level: 'error',
        });
      } finally {
        closeOverlay(overlay);
      }
    });
  }

  render() {
    return div();
  }
}
