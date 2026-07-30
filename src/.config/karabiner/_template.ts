/**
 *  This file is used to generate the karabiner.json file.
 *  You can run it via node (eg. node _template.ts > karabiner.json)
 *  Use the .env at root to set the LOCAL_PW
 *
 *  The config is split across sibling modules:
 *   - constants.ts : global variable names, key maps, condition arrays, env values
 *   - helper.ts    : reusable manipulator generators
 *   - profile.ts   : devices, fn_function_keys, simple_modifications
 *   - rules/       : complex_modifications rules grouped by scope (mode/global/apps/devices)
 */

import { devices, fnFunctionKeys, simpleModifications } from './profile.ts';
import { rules } from './rules/index.ts';

const karabinerConfig = {
  profiles: [
    {
      name: '1',
      selected: true,
      virtual_hid_keyboard: { country_code: 0, keyboard_type_v2: 'ansi' },
      devices,
      fn_function_keys: fnFunctionKeys,
      simple_modifications: simpleModifications,
      complex_modifications: { rules },
    },
    {
      name: 'No maps',
      virtual_hid_keyboard: { country_code: 0, keyboard_type_v2: 'ansi' },
      complex_modifications: { rules: [] },
    },
  ],
};
console.log(JSON.stringify(karabinerConfig, null, 2));
