/**
 * "Mode - *" complex modification rules.
 */

import {
  F18_IS_DOWN,
  VIM_KEYS,
  VIM_SHIFT_DOWN,
  VIM_SHIFT_KEY,
} from '../constants.ts';

export const modeRules = [
  {
    description: 'Mode - VIM',
    manipulators: VIM_KEYS.flatMap<unknown[]>(({ key, to }) => [
      {
        type: 'basic',
        conditions: [
          { name: F18_IS_DOWN, type: 'variable_if', value: 1 },
          { name: VIM_SHIFT_DOWN, type: 'variable_if', value: 1 },
        ],
        from: { key_code: key, modifiers: { optional: ['any'] } },
        to: { key_code: to, modifiers: ['left_shift'] },
      },
      {
        type: 'basic',
        conditions: [{ name: F18_IS_DOWN, type: 'variable_if', value: 1 }],
        from: { key_code: key, modifiers: { optional: ['any'] } },
        to: { key_code: to },
      },
    ]).concat([
      {
        type: 'basic',
        conditions: [{ name: F18_IS_DOWN, type: 'variable_if', value: 1 }],
        from: {
          key_code: VIM_SHIFT_KEY,
          modifiers: { optional: ['any'] },
        },
        to: [{ set_variable: { name: VIM_SHIFT_DOWN, value: 1 } }],
        to_after_key_up: [{ set_variable: { name: VIM_SHIFT_DOWN, value: 0 } }],
      },
    ]),
  },
  {
    description: 'Mode - Click',
    manipulators: [
      {
        type: 'basic',
        conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
        from: {
          key_code: 'c',
          modifiers: { mandatory: ['left_option'], optional: ['any'] },
        },
        to: [{ pointing_button: 'button2' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'c',
          modifiers: { mandatory: ['left_option'], optional: ['any'] },
        },
        to: [{ pointing_button: 'button1' }],
      },
    ],
  },
];
