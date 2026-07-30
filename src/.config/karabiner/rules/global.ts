/**
 * "Global - *" complex modification rules (active regardless of app/device).
 */

import { F18_IS_DOWN, LOCAL_PW } from '../constants.ts';
import {
  doubleTapToManipupators,
  getKarabinerEventFromLetter,
} from '../helper.ts';

const localPwManipulators = LOCAL_PW
  ? [
      {
        type: 'basic',
        from: {
          key_code: 'v',
          modifiers: { mandatory: ['left_option'] },
        },
        to: Array.from(LOCAL_PW).map(getKarabinerEventFromLetter),
      },
    ]
  : [];

export const globalRules = [
  {
    description: 'Global - CapsLock to F18',
    manipulators: [
      {
        type: 'basic',
        from: { key_code: 'f18', modifiers: { optional: ['any'] } },
        parameters: { 'basic.to_if_alone_timeout_milliseconds': 300 },
        to: [{ set_variable: { name: 'f18isDown', value: 1 } }],
        to_after_key_up: [{ set_variable: { name: 'f18isDown', value: 0 } }],
        to_if_alone: [{ key_code: 'escape' }],
      },
    ],
  },
  {
    description: 'Global - Capslock as Control for some keys',
    manipulators: ['c', 'v', 'e', 'spacebar', 'tab'].map((key) => ({
      type: 'basic',
      conditions: [{ name: F18_IS_DOWN, type: 'variable_if', value: 1 }],
      from: { key_code: key, modifiers: { optional: ['any'] } },
      to: [{ key_code: key, modifiers: ['left_control'] }],
    })),
  },
  {
    description:
      'Global - Cmd[shift] + J/K to PageDown/PageUp and restore it with Fn + J/K',
    manipulators: [
      {
        type: 'basic',
        from: {
          key_code: 'j',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['left_shift', 'caps_lock'],
          },
        },
        to: [{ key_code: 'page_down' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'k',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['left_shift', 'caps_lock'],
          },
        },
        to: [{ key_code: 'page_up' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'j',
          modifiers: { mandatory: ['fn'], optional: ['any'] },
        },
        to: [{ key_code: 'j', modifiers: ['left_command'] }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'k',
          modifiers: { mandatory: ['fn'], optional: ['any'] },
        },
        to: [{ key_code: 'k', modifiers: ['left_command'] }],
      },
    ],
  },
  {
    description: 'Global - App Exposé',
    manipulators: [
      {
        type: 'basic',
        from: {
          key_code: 'j',
          modifiers: {
            mandatory: ['left_command', 'left_option'],
            optional: ['caps_lock'],
          },
        },
        to: [{ key_code: 'down_arrow', modifiers: ['left_control'] }],
      },
    ],
  },
  {
    description: 'Global - Alt + m to mute mic',
    manipulators: [
      {
        type: 'basic',
        from: {
          key_code: 'm',
          modifiers: { mandatory: ['left_option'] },
        },
        to: [{ key_code: '0', modifiers: ['left_option', 'left_command'] }],
      },
    ],
  },
  {
    description: 'Global - Double Fn to Cmd + option + 9 (whisperer)',
    manipulators: doubleTapToManipupators({
      type: 'vendor',
      key: 'keyboard_fn',
      globalVar: 'g_whisperer_pressed',
      to: [{ key_code: '9', modifiers: ['left_command', 'left_option'] }],
    }),
  },
  {
    description: 'Global - Double Shift to Capslock',
    manipulators: doubleTapToManipupators({
      key: 'left_shift',
      to: [{ key_code: 'caps_lock' }],
      globalVar: 'g_shift_pressed',
    }),
  },
  {
    description: 'Global - Function Keys',
    manipulators: [
      {
        type: 'basic',
        from: {
          key_code: 'f1',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'display_brightness_decrement' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f2',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'display_brightness_increment' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f7',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'rewind' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f8',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'play_or_pause' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f9',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'fast_forward' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f10',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'mute' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f11',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'volume_decrement' }],
      },
      {
        type: 'basic',
        from: {
          key_code: 'f12',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ consumer_key_code: 'volume_increment' }],
      },
    ],
  },
  {
    description: 'Global - Local PW',
    manipulators: localPwManipulators,
  },
];
