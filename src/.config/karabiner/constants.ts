/**
 * Shared constants for the Karabiner config: global variable names, key maps,
 * reusable condition arrays, and env-derived values.
 */

// @ts-expect-error - no definitions
import { fileURLToPath } from 'node:url';

try {
  // @ts-expect-error - process.loadEnvFile is not defined in the type definitions
  process.loadEnvFile(fileURLToPath(import.meta.resolve('../../../.env')));
} catch (error: unknown) {
  console.warn(
    "Warning: couldn't load .env file, perhaps it doesn't exist:",
    (error as Error)?.message,
  );
}

// @ts-expect-error - process.env is not defined in the type definitions
export const LOCAL_PW = process.env.LOCAL_PW;

export const F18_IS_DOWN = 'f18isDown';
export const VIM_SHIFT_DOWN = 'vimShiftDown';
export const VIM_SHIFT_KEY = 'f';
export const VIM_KEYS = [
  { key: 'h', to: 'left_arrow' },
  { key: 'j', to: 'down_arrow' },
  { key: 'k', to: 'up_arrow' },
  { key: 'l', to: 'right_arrow' },
];

export const googleChromeConditions = [
  {
    type: 'frontmost_application_if',
    bundle_identifiers: ['com.google.Chrome'],
  },
];
export const ankiLauncherConditions = [
  {
    type: 'frontmost_application_if',
    bundle_identifiers: ['net.ankiweb.launcher'],
  },
];
export const vocabulerApprConditions = [
  {
    type: 'frontmost_application_if',
    file_paths: ['/Vocabuler\\.app/'],
  },
];
export const g10ControlConditions = [
  { type: 'device_if', identifiers: [{ vendor_id: 6421, product_id: 4133 }] },
];
export const f3f4CmdHCmdLTabberConditions = [
  {
    type: 'frontmost_application_if',
    bundle_identifiers: [
      'com.google.Chrome',
      'com.apple.finder',
      'dev.warp.Warp-Stable',
      'com.apple.dt.Xcode',
      'app.supabit.supacode',
    ],
  },
];
