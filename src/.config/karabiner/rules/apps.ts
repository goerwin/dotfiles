/**
 * "Apps (...)" complex modification rules (scoped to the frontmost app).
 */

import {
  f3f4CmdHCmdLTabberConditions,
  googleChromeConditions,
} from '../constants.ts';

export const appsRules = [
  {
    description:
      'Apps (Finder, Google Chrome, Warp, Xcode) - Cmd + H/L and F3/F4 to prev/next tab',
    manipulators: [
      {
        type: 'basic',
        conditions: f3f4CmdHCmdLTabberConditions,
        from: {
          key_code: 'h',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['caps_lock'],
          },
        },
        to: [
          {
            key_code: 'tab',
            modifiers: ['left_control', 'left_shift'],
          },
        ],
      },
      {
        type: 'basic',
        conditions: f3f4CmdHCmdLTabberConditions,
        from: {
          key_code: 'l',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['caps_lock'],
          },
        },
        to: [{ key_code: 'tab', modifiers: ['left_control'] }],
      },
      {
        type: 'basic',
        conditions: f3f4CmdHCmdLTabberConditions,
        from: {
          key_code: 'f3',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [
          {
            key_code: 'tab',
            modifiers: ['left_control', 'left_shift'],
          },
        ],
      },
      {
        type: 'basic',
        conditions: f3f4CmdHCmdLTabberConditions,
        from: {
          key_code: 'f4',
          modifiers: { optional: ['caps_lock'] },
        },
        to: [{ key_code: 'tab', modifiers: ['left_control'] }],
      },
    ],
  },
  {
    description: 'Apps (Google Chrome) - Cmd + ; to Cmd + L',
    manipulators: [
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: {
          key_code: 'semicolon',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['caps_lock'],
          },
        },
        to: [{ key_code: 'l', modifiers: ['left_command'] }],
      },
    ],
  },
  {
    description: 'Apps (Google Chrome) - F5 to Alt + M and F6 to Alt + T',
    manipulators: [
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: { key_code: 'f5' },
        to: [{ key_code: 'm', modifiers: ['left_option'] }],
      },
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: { key_code: 'f6' },
        to: [{ key_code: 't', modifiers: ['left_option'] }],
      },
    ],
  },
  {
    description: 'Apps (Google Chrome) - Toggle full-screen',
    manipulators: [
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: {
          key_code: 'f',
          modifiers: { mandatory: ['left_command', 'left_option'] },
        },
        to: [
          {
            key_code: 'f',
            modifiers: ['left_command', 'left_control'],
          },
        ],
      },
    ],
  },
  {
    description: 'Apps (Google Chrome) - Unfocus omnibar',
    manipulators: [
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: {
          key_code: 'e',
          modifiers: {
            mandatory: ['left_command'],
            optional: ['caps_lock'],
          },
        },
        to: [
          { key_code: 'l', modifiers: ['left_command'] },
          { key_code: 'j' },
          { key_code: 'a' },
          { key_code: 'v' },
          { key_code: 'a' },
          { key_code: 's' },
          { key_code: 'c' },
          { key_code: 'r' },
          { key_code: 'i' },
          { key_code: 'p' },
          { key_code: 't' },
          { key_code: 'semicolon', modifiers: ['left_shift'] },
          { key_code: 'semicolon' },
          { key_code: 'return_or_enter' },
        ],
      },
    ],
  },
  {
    description: 'Apps (Google Chrome) - Cmd + shift + i to toggle dev tools',
    manipulators: [
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: {
          key_code: 'i',
          modifiers: {
            mandatory: ['left_command', 'left_shift'],
            optional: ['caps_lock'],
          },
        },
        to: [{ key_code: 'i', modifiers: ['left_command', 'left_option'] }],
      },
      {
        type: 'basic',
        conditions: googleChromeConditions,
        from: { key_code: 'f6' },
        to: [{ key_code: 't', modifiers: ['left_option'] }],
      },
    ],
  },
  {
    description: 'Apps (Slack) - Cmd + P to search',
    manipulators: [
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['com.tinyspeck.slackmacgap'],
            type: 'frontmost_application_if',
          },
        ],
        from: {
          key_code: 'p',
          modifiers: { mandatory: ['left_command'] },
        },
        to: [{ key_code: 'k', modifiers: ['left_command'] }],
      },
    ],
  },
  {
    description: 'Apps (Supacode) - Cmd + O to clear terminal',
    manipulators: [
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['app.supabit.supacode'],
            type: 'frontmost_application_if',
          },
        ],
        from: {
          key_code: 'o',
          modifiers: { mandatory: ['left_command'] },
        },
        to: [{ key_code: 'k', modifiers: ['left_command'] }],
      },
    ],
  },
  {
    description: 'Apps (Starcraft2) - Modifications',
    manipulators: [
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['com.blizzard.starcraft2'],
            type: 'frontmost_application_if',
          },
        ],
        from: {
          key_code: 'd',
          modifiers: { mandatory: ['left_command'] },
        },
        to: [{ key_code: 'c', modifiers: ['left_option'] }],
      },
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['com.blizzard.starcraft2'],
            type: 'frontmost_application_unless',
          },
        ],
        from: {
          key_code: 'f1',
          modifiers: { mandatory: ['left_command'], optional: ['any'] },
        },
        to: [{ key_code: 'f1' }],
      },
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['com.blizzard.starcraft2'],
            type: 'frontmost_application_unless',
          },
        ],
        from: {
          key_code: 'f2',
          modifiers: { mandatory: ['left_command'], optional: ['any'] },
        },
        to: [{ key_code: 'f2' }],
      },
      {
        type: 'basic',
        conditions: [
          {
            bundle_identifiers: ['com.blizzard.starcraft2'],
            type: 'frontmost_application_unless',
          },
        ],
        from: { key_code: 'f10' },
        to: [{ consumer_key_code: 'mute' }],
      },
    ],
  },
];
