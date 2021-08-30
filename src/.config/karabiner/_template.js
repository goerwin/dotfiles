// Use this to generate karabiner.json file
// This allows for sharing config as needed

/**
# cd to dotfiles folder and run
node src/.config/karabiner/_template.js > src/.config/karabiner/karabiner.json
 */

const fnFuntionKeys = [
  {
    from: { key_code: 'f1' },
    to: { key_code: 'f1' },
    // to: [{ consumer_key_code: 'display_brightness_decrement' }],
  },
  {
    from: { key_code: 'f2' },
    to: { key_code: 'f2' },
    // to: [{ consumer_key_code: 'display_brightness_increment' }],
  },
  {
    from: { key_code: 'f3' },
    to: { key_code: 'f3' },
    // to: [{ apple_vendor_keyboard_key_code: 'mission_control' }],
  },
  {
    from: { key_code: 'f4' },
    to: { key_code: 'f4' },
    // to: [{ apple_vendor_keyboard_key_code: 'spotlight' }],
  },
  {
    from: { key_code: 'f5' },
    to: { key_code: 'f5' },
    // to: [{ consumer_key_code: 'dictation' }],
  },
  {
    from: { key_code: 'f6' },
    to: { key_code: 'f6' },
    // to: [{ key_code: 'f6' }],
  },
  {
    from: { key_code: 'f7' },
    to: { key_code: 'f7' },
    // to: [{ consumer_key_code: 'rewind' }],
  },
  {
    from: { key_code: 'f8' },
    to: { key_code: 'f8' },
    // to: [{ consumer_key_code: 'play_or_pause' }],
  },
  {
    from: { key_code: 'f9' },
    to: { key_code: 'f9' },
    // to: [{ consumer_key_code: 'fast_forward' }],
  },
  {
    from: { key_code: 'f10' },
    to: { key_code: 'f10' },
    // to: [{ consumer_key_code: 'mute' }],
  },
  {
    from: { key_code: 'f11' },
    to: { key_code: 'f11' },
    // to: [{ consumer_key_code: 'volume_decrement' }],
  },
  {
    from: { key_code: 'f12' },
    to: { key_code: 'f12' },
    // to: [{ consumer_key_code: 'volume_increment' }],
  },
];

const switchProfileShortcuts = {
  description: 'Global - Switch profiles shortcuts',
  manipulators: [
    {
      from: { simultaneous: [{ key_code: 'escape' }, { key_code: '1' }] },
      parameters: { 'basic.simultaneous_threshold_milliseconds': 1000 },
      to: [
        {
          shell_command:
            "'/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli' --select-profile '1'",
        },
      ],
      type: 'basic',
    },
    {
      from: { simultaneous: [{ key_code: 'escape' }, { key_code: '2' }] },
      parameters: { 'basic.simultaneous_threshold_milliseconds': 1000 },
      to: [
        {
          shell_command:
            "'/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli' --select-profile '2'",
        },
      ],
      type: 'basic',
    },
    {
      conditions: [
        { name: 'doubleEscToToggleMaps', type: 'variable_if', value: 1 },
      ],
      from: { key_code: 'escape', modifiers: { optional: ['caps_lock'] } },
      to_after_key_up: [
        {
          shell_command:
            "'/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli' --select-profile 'No maps'",
        },
      ],
      to_if_held_down: [{ halt: true, key_code: 'escape' }],
      type: 'basic',
    },
    {
      from: { key_code: 'escape', modifiers: { optional: ['any'] } },
      to: [
        { set_variable: { name: 'doubleEscToToggleMaps', value: 1 } },
        { key_code: 'escape' },
      ],
      to_delayed_action: {
        to_if_canceled: [
          { set_variable: { name: 'doubleEscToToggleMaps', value: 0 } },
        ],
        to_if_invoked: [
          { set_variable: { name: 'doubleEscToToggleMaps', value: 0 } },
        ],
      },
      type: 'basic',
    },
  ],
};

const profile1 = {
  complex_modifications: {
    parameters: {
      'basic.simultaneous_threshold_milliseconds': 50,
      'basic.to_delayed_action_delay_milliseconds': 500,
      'basic.to_if_alone_timeout_milliseconds': 1000,
      'basic.to_if_held_down_threshold_milliseconds': 500,
      'mouse_motion_to_scroll.speed': 100,
    },
    rules: [
      {
        description: 'Mode::VIM',
        manipulators: [
          {
            conditions: [
              { name: 'f18isDown', type: 'variable_if', value: 1 },
              { name: 'vimShiftDown', type: 'variable_if', value: 1 },
            ],
            from: { key_code: 'h', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'left_arrow', modifiers: ['left_shift'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'h', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'left_arrow' }],
            type: 'basic',
          },
          {
            conditions: [
              { name: 'f18isDown', type: 'variable_if', value: 1 },
              { name: 'vimShiftDown', type: 'variable_if', value: 1 },
            ],
            from: { key_code: 'j', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'down_arrow', modifiers: ['left_shift'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'j', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'down_arrow' }],
            type: 'basic',
          },
          {
            conditions: [
              { name: 'f18isDown', type: 'variable_if', value: 1 },
              { name: 'vimShiftDown', type: 'variable_if', value: 1 },
            ],
            from: { key_code: 'k', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'up_arrow', modifiers: ['left_shift'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'k', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'up_arrow' }],
            type: 'basic',
          },
          {
            conditions: [
              { name: 'f18isDown', type: 'variable_if', value: 1 },
              { name: 'vimShiftDown', type: 'variable_if', value: 1 },
            ],
            from: { key_code: 'l', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'right_arrow', modifiers: ['left_shift'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'l', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'right_arrow' }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'f', modifiers: { optional: ['any'] } },
            to: [{ set_variable: { name: 'vimShiftDown', value: 1 } }],
            to_after_key_up: [
              { set_variable: { name: 'vimShiftDown', value: 0 } },
            ],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Mode::Click',
        manipulators: [
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: {
              key_code: 'c',
              modifiers: { mandatory: ['left_option'], optional: ['any'] },
            },
            to: [{ pointing_button: 'button2' }],
            type: 'basic',
          },
          {
            from: {
              key_code: 'c',
              modifiers: { mandatory: ['left_option'], optional: ['any'] },
            },
            to: [{ pointing_button: 'button1' }],
            type: 'basic',
          },
        ],
      },
      {
        description:
          'App::Google Chrome::Terminal - Cmd + H/L and F3/F4 to prev/next tab',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: [
                  '^com\\.google\\.Chrome$',
                  '^com\\.apple\\.Terminal$',
                ],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'h', modifiers: { mandatory: ['left_command'] } },
            to: [
              { key_code: 'tab', modifiers: ['left_control', 'left_shift'] },
            ],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: [
                  '^com\\.google\\.Chrome$',
                  '^com\\.apple\\.Terminal$',
                ],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'l', modifiers: { mandatory: ['left_command'] } },
            to: [{ key_code: 'tab', modifiers: ['left_control'] }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: [
                  '^com\\.google\\.Chrome$',
                  '^com\\.apple\\.Terminal$',
                ],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'f3' },
            to: [
              { key_code: 'tab', modifiers: ['left_control', 'left_shift'] },
            ],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: [
                  '^com\\.google\\.Chrome$',
                  '^com\\.apple\\.Terminal$',
                ],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'f4' },
            to: [{ key_code: 'tab', modifiers: ['left_control'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Google Chrome - Cmd + ; to Cmd + L',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: {
              key_code: 'semicolon',
              modifiers: { mandatory: ['left_command'] },
            },
            to: [{ key_code: 'l', modifiers: ['left_command'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Google Chrome - Toggle full-screen',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: {
              key_code: 'f',
              modifiers: { mandatory: ['left_command', 'left_option'] },
            },
            to: [
              { key_code: 'f', modifiers: ['left_command', 'left_control'] },
            ],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Google Chrome - F5 to Alt + M and F6 to Alt + T',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'f5' },
            to: [{ key_code: 'm', modifiers: ['left_option'] }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'f6' },
            to: [{ key_code: 't', modifiers: ['left_option'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Google Chrome - Cmd + shift + i to toggle dev tools',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: {
              key_code: 'i',
              modifiers: { mandatory: ['left_command', 'left_shift'] },
            },
            to: [{ key_code: 'i', modifiers: ['left_command', 'left_option'] }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.google\\.Chrome$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'f6' },
            to: [{ key_code: 't', modifiers: ['left_option'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::iTerm - Cmd + O to clean console',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.googlecode\\.iterm2$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'o', modifiers: { mandatory: ['left_command'] } },
            to: [{ key_code: 'k', modifiers: ['left_command'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Slack - Toggle full-screen',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.tinyspeck\\.slackmacgap$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'p', modifiers: { mandatory: ['left_command'] } },
            to: [{ key_code: 'k', modifiers: ['left_command'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'App::Starcraft2 - modifications',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_if',
              },
            ],
            from: { key_code: 'd', modifiers: { mandatory: ['left_command'] } },
            to: [{ key_code: 'c', modifiers: ['left_option'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Double Shift to CAPS',
        manipulators: [
          {
            conditions: [
              { name: 'doubleShiftToCaps', type: 'variable_if', value: 1 },
            ],
            from: {
              key_code: 'left_shift',
              modifiers: { optional: ['caps_lock'] },
            },
            to_after_key_up: [{ key_code: 'caps_lock' }],
            to_if_held_down: [{ halt: true, key_code: 'left_shift' }],
            type: 'basic',
          },
          {
            from: { key_code: 'left_shift', modifiers: { optional: ['any'] } },
            to: [
              { set_variable: { name: 'doubleShiftToCaps', value: 1 } },
              { key_code: 'left_shift' },
            ],
            to_delayed_action: {
              to_if_canceled: [
                { set_variable: { name: 'doubleShiftToCaps', value: 0 } },
              ],
              to_if_invoked: [
                { set_variable: { name: 'doubleShiftToCaps', value: 0 } },
              ],
            },
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - CapsLock to F18',
        manipulators: [
          {
            from: { key_code: 'f18', modifiers: { optional: ['any'] } },
            parameters: { 'basic.to_if_alone_timeout_milliseconds': 300 },
            to: [{ set_variable: { name: 'f18isDown', value: 1 } }],
            to_after_key_up: [
              { set_variable: { name: 'f18isDown', value: 0 } },
            ],
            to_if_alone: [{ key_code: 'escape' }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Capslock as Control for somekeys',
        manipulators: [
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'c', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'c', modifiers: ['left_control'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'v', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'v', modifiers: ['left_control'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'spacebar', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'spacebar', modifiers: ['left_control'] }],
            type: 'basic',
          },
          {
            conditions: [{ name: 'f18isDown', type: 'variable_if', value: 1 }],
            from: { key_code: 'tab', modifiers: { optional: ['any'] } },
            to: [{ key_code: 'tab', modifiers: ['left_control'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Alt + H/L to Cmd + Left/Right',
        manipulators: [
          {
            from: { key_code: 'h', modifiers: { mandatory: ['left_option'] } },
            to: [{ key_code: 'left_arrow', modifiers: ['left_command'] }],
            type: 'basic',
          },
          {
            from: { key_code: 'l', modifiers: { mandatory: ['left_option'] } },
            to: [{ key_code: 'right_arrow', modifiers: ['left_command'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Cmd[shift] + J/K to PageDown/PageUp',
        manipulators: [
          {
            from: {
              key_code: 'j',
              modifiers: {
                mandatory: ['left_command'],
                optional: ['left_shift'],
              },
            },
            to: [{ key_code: 'page_down' }],
            type: 'basic',
          },
          {
            from: {
              key_code: 'k',
              modifiers: {
                mandatory: ['left_command'],
                optional: ['left_shift'],
              },
            },
            to: [{ key_code: 'page_up' }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - App Exposé',
        manipulators: [
          {
            from: {
              key_code: 'j',
              modifiers: { mandatory: ['left_command', 'left_option'] },
            },
            to: [{ key_code: 'down_arrow', modifiers: ['left_control'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Alt + m to mute mic',
        manipulators: [
          {
            from: { key_code: 'm', modifiers: { mandatory: ['left_option'] } },
            to: [{ key_code: 'm', modifiers: ['left_option', 'left_command'] }],
            type: 'basic',
          },
        ],
      },
      {
        description: 'Global - Function Keys',
        manipulators: [
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_unless',
              },
            ],
            from: { key_code: 'f1' },
            to: [{ consumer_key_code: 'display_brightness_decrement' }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_unless',
              },
            ],
            from: {
              key_code: 'f1',
              modifiers: { mandatory: ['left_command'], optional: ['any'] },
            },
            to: [{ key_code: 'f1' }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_unless',
              },
            ],
            from: { key_code: 'f2' },
            to: [{ consumer_key_code: 'display_brightness_increment' }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_unless',
              },
            ],
            from: {
              key_code: 'f2',
              modifiers: { mandatory: ['left_command'], optional: ['any'] },
            },
            to: [{ key_code: 'f2' }],
            type: 'basic',
          },
          {
            conditions: [
              {
                bundle_identifiers: ['^com\\.blizzard\\.starcraft2$'],
                type: 'frontmost_application_unless',
              },
            ],
            from: { key_code: 'f10' },
            to: [{ consumer_key_code: 'mute' }],
            type: 'basic',
          },
          {
            from: {
              key_code: 'f10',
              modifiers: { mandatory: ['left_command'], optional: ['any'] },
            },
            to: [{ key_code: 'f10' }],
            type: 'basic',
          },
          {
            from: { key_code: 'f11' },
            to: [{ consumer_key_code: 'volume_decrement' }],
            type: 'basic',
          },
          {
            from: {
              key_code: 'f11',
              modifiers: { mandatory: ['left_command'], optional: ['any'] },
            },
            to: [{ key_code: 'f11' }],
            type: 'basic',
          },
          {
            from: { key_code: 'f12' },
            to: [{ consumer_key_code: 'volume_increment' }],
            type: 'basic',
          },
          {
            from: {
              key_code: 'f12',
              modifiers: { mandatory: ['left_command'], optional: ['any'] },
            },
            to: [{ key_code: 'f12' }],
            type: 'basic',
          },
        ],
      },
      switchProfileShortcuts,
    ],
  },
  devices: [
    {
      // CM Storm keyboard
      disable_built_in_keyboard_if_exists: false,
      fn_function_keys: [],
      identifiers: {
        is_keyboard: true,
        is_pointing_device: false,
        product_id: 32,
        vendor_id: 9494,
      },
      ignore: false,
      manipulate_caps_lock_led: true,
      simple_modifications: [
        {
          from: { key_code: 'left_command' },
          to: [{ key_code: 'left_option' }],
        },
        {
          from: { key_code: 'left_option' },
          to: [{ key_code: 'left_command' }],
        },
        {
          from: { key_code: 'right_command' },
          to: [{ key_code: 'left_option' }],
        },
        {
          from: { key_code: 'right_option' },
          to: [{ key_code: 'left_command' }],
        },
        {
          from: { key_code: 'grave_accent_and_tilde' },
          to: [{ key_code: 'grave_accent_and_tilde' }],
        },
      ],
    },
  ],
  fn_function_keys: fnFuntionKeys,
  name: '1',
  parameters: {
    delay_milliseconds_before_open_device: 1000,
  },
  selected: true,
  simple_modifications: [
    {
      from: { key_code: 'caps_lock' },
      to: [{ key_code: 'f18' }],
    },
    {
      from: { key_code: 'grave_accent_and_tilde' },
      to: [{ key_code: 'left_shift' }],
    },
    {
      from: { key_code: 'non_us_backslash' },
      to: [{ key_code: 'grave_accent_and_tilde' }],
    },
    {
      from: { key_code: 'right_command' },
      to: [{ key_code: 'left_command' }],
    },
    { from: { key_code: 'right_shift' }, to: [{ key_code: 'left_shift' }] },
  ],
  virtual_hid_keyboard: {
    country_code: 0,
    indicate_sticky_modifier_keys_state: true,
    mouse_key_xy_scale: 100,
  },
};

console.log(
  JSON.stringify(
    {
      global: {
        check_for_updates_on_startup: true,
        show_in_menu_bar: true,
        show_profile_name_in_menu_bar: true,
      },
      profiles: [
        profile1,
        {
          ...profile1,
          name: '2',
          selected: false,
          complex_modifications: {
            ...profile1.complex_modifications,
            rules: [
              ...profile1.complex_modifications.rules,
              {
                description: 'Global - Twitch Mode',
                manipulators: [
                  {
                    from: { key_code: 'up_arrow' },
                    to: [{ key_code: 'm', modifiers: ['left_option'] }],
                    type: 'basic',
                  },
                  {
                    from: { key_code: 'down_arrow' },
                    to: [{ key_code: 't', modifiers: ['left_option'] }],
                    type: 'basic',
                  },
                  {
                    from: { key_code: 'left_arrow' },
                    to: [
                      {
                        key_code: 'tab',
                        modifiers: ['left_control', 'left_shift'],
                      },
                    ],
                    type: 'basic',
                  },
                  {
                    from: { key_code: 'right_arrow' },
                    to: [{ key_code: 'tab', modifiers: ['left_control'] }],
                    type: 'basic',
                  },
                ],
              },
            ],
          },
        },
        {
          complex_modifications: {
            parameters: {
              'basic.simultaneous_threshold_milliseconds': 50,
              'basic.to_delayed_action_delay_milliseconds': 500,
              'basic.to_if_alone_timeout_milliseconds': 1000,
              'basic.to_if_held_down_threshold_milliseconds': 500,
              'mouse_motion_to_scroll.speed': 100,
            },
            rules: [switchProfileShortcuts],
          },
          devices: [],
          fn_function_keys: fnFuntionKeys,
          name: 'No maps',
          parameters: {
            delay_milliseconds_before_open_device: 1000,
          },
          selected: false,
          simple_modifications: [],
          virtual_hid_keyboard: {
            country_code: 0,
            indicate_sticky_modifier_keys_state: true,
            mouse_key_xy_scale: 100,
          },
        },
      ],
    },
    null,
    2
  )
);
