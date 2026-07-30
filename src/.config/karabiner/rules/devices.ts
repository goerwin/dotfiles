/**
 * "Device - *" complex modification rules (scoped to specific hardware).
 */

import {
  ankiLauncherConditions,
  g10ControlConditions,
  googleChromeConditions,
  vocabulerApprConditions,
} from '../constants.ts';

export const deviceRules = [
  {
    description: 'Device - G10 Control - Apps (Anki)',
    manipulators: [
      {
        description: 'Left to 1',
        type: 'basic',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { key_code: 'left_arrow' },
        to: [{ key_code: '1' }],
      },
      {
        description: 'Right to 4',
        type: 'basic',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { key_code: 'right_arrow' },
        to: [{ key_code: '4' }],
      },
      {
        description: 'Back to D',
        type: 'basic',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'ac_back' },
        to: [{ key_code: 'd' }],
      },
      {
        description: 'Down to Tab',
        type: 'basic',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { key_code: 'down_arrow' },
        to: [{ key_code: 'tab' }],
      },
      {
        type: 'basic',
        description: 'Up to Shift + Tab',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { key_code: 'up_arrow' },
        to: [{ key_code: 'tab', modifiers: ['left_shift'] }],
      },
      {
        type: 'basic',
        description: 'Play/Pause to R',
        conditions: [...ankiLauncherConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'play_or_pause' },
        to: [{ key_code: 'r' }],
      },
    ],
  },
  {
    description: 'Device - G10 Control - Apps (Vocabuler)',
    manipulators: [
      {
        description: 'ac_back to Shift + Tab',
        type: 'basic',
        conditions: [...vocabulerApprConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'ac_back' },
        to: [{ key_code: 'tab', modifiers: ['left_shift'] }],
      },
      {
        description: 'Application to Tab',
        type: 'basic',
        conditions: [...vocabulerApprConditions, ...g10ControlConditions],
        from: { key_code: 'application' },
        to: [{ key_code: 'tab' }],
      },
      {
        description: 'Enter to Space',
        type: 'basic',
        conditions: [...vocabulerApprConditions, ...g10ControlConditions],
        from: { key_code: 'return_or_enter' },
        to: [{ key_code: 'spacebar' }],
      },
      {
        description: 'Mic to Enter',
        type: 'basic',
        conditions: [...vocabulerApprConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'dictation' },
        to: [{ key_code: 'return_or_enter' }],
      },
      {
        description: 'Play/Pause to `',
        type: 'basic',
        conditions: [...vocabulerApprConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'play_or_pause' },
        to: [{ key_code: 'grave_accent_and_tilde' }],
      },
    ],
  },
  {
    description: 'Device - G10 Control - Apps (Google Chrome)',
    manipulators: [
      {
        description: 'Enter to Space',
        type: 'basic',
        conditions: [...googleChromeConditions, ...g10ControlConditions],
        from: { key_code: 'return_or_enter' },
        to: [{ key_code: 'spacebar' }],
      },
      {
        description: 'Play/Pause to Escape',
        type: 'basic',
        conditions: [...googleChromeConditions, ...g10ControlConditions],
        from: { consumer_key_code: 'play_or_pause' },
        to: [{ key_code: 'escape' }],
      },
    ],
  },
  {
    description: 'Device - G10 Control',
    manipulators: [
      {
        description: 'Page Down to Volume Down',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { key_code: 'page_down' },
        to: [{ consumer_key_code: 'volume_decrement' }],
      },
      {
        description: 'Page Up to Volume Up',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { key_code: 'page_up' },
        to: [{ consumer_key_code: 'volume_increment' }],
      },
      {
        description: 'Volume Down to Brightness Down',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { consumer_key_code: 'volume_decrement' },
        to: [{ consumer_key_code: 'display_brightness_decrement' }],
      },
      {
        description: 'Volume Up to Brightness Up',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { consumer_key_code: 'volume_increment' },
        to: [{ consumer_key_code: 'display_brightness_increment' }],
      },
      {
        description: 'Delete[Hold] to Ctrl + Shift + Tab [Close tab: Cmd + W]',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { key_code: 'delete_or_backspace' },
        to_if_alone: [
          {
            key_code: 'tab',
            modifiers: ['left_control', 'left_shift'],
          },
        ],
        to_if_held_down: [
          {
            key_code: 'w',
            modifiers: ['left_command'],
            repeat: false,
            halt: true,
          },
        ],
      },
      {
        description: 'Mute[Hold] to Ctrl + Tab [App switcher: Cmd + Tab]',
        type: 'basic',
        conditions: g10ControlConditions,
        from: { consumer_key_code: 'mute' },
        to_if_alone: [
          {
            key_code: 'tab',
            modifiers: ['left_control'],
            repeat: false,
          },
        ],
        to_if_held_down: [
          {
            key_code: 'tab',
            modifiers: ['left_command', 'left_shift'],
            repeat: false,
            halt: true,
          },
        ],
      },
    ],
  },
];
