/**
 * Ordered list of all complex modification rules.
 * Order is preserved from the original config (Mode -> Global -> Apps -> Device).
 */

import { appsRules } from './apps.ts';
import { deviceRules } from './devices.ts';
import { globalRules } from './global.ts';
import { modeRules } from './mode.ts';

export const rules = [
  ...modeRules,
  ...globalRules,
  ...appsRules,
  ...deviceRules,
];
