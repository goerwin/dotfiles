/**
 * Ordered list of all complex modification rules.
 * Most specific first (Mode -> Devices -> Apps -> Global), same order as
 * keyRemapperMac/config.json rules.
 */

import { appsRules } from './apps.ts';
import { deviceRules } from './devices.ts';
import { globalRules } from './global.ts';
import { modeRules } from './mode.ts';

export const rules = [
  ...modeRules,
  ...deviceRules,
  ...appsRules,
  ...globalRules,
];
