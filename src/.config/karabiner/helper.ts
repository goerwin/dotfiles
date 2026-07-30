/**
 * Generates the Karabiner Event from a letter
 * @param letter - letter to be converted
 * @returns Karabiner event representation of the letter
 */
export function getKarabinerEventFromLetter(letter: unknown) {
  if (typeof letter !== 'string') return null;

  if (/[a-z0-9]/.test(letter)) {
    return {
      key_code: letter,
    };
  }

  if (/[A-Z]/.test(letter)) {
    return {
      key_code: letter.toLowerCase(),
      modifiers: ['left_shift'],
    };
  }

  if (letter === '$') {
    return {
      key_code: '4',
      modifiers: ['left_shift'],
    };
  }

  return null;
}

/**
 * Generates the Karabiner Event from a long tap on a key
 *
 * @param args - Arguments for the long tap to manipupators
 * @param args.key - The key to be tapped
 * @param args.to - The manipupators to be applied when the key is held down
 * @param args.type - The type of key to be tapped, either 'normal' or 'vendor'
 *
 * @returns Karabiner event representation of the long tap to manipupators
 */
export function longTapToManipupators(args: {
  key: string;
  to: unknown;
  type?: 'normal' | 'vendor';
}) {
  const { key, to, type = 'normal' } = args;
  const keyType =
    type === 'normal' ? 'key_code' : 'apple_vendor_top_case_key_code';

  return [
    {
      type: 'basic',
      from: { [keyType]: key, modifiers: { optional: ['any'] } },
      to_if_alone: [{ [keyType]: key }],
      to_if_held_down: to,
      parameters: {
        'basic.to_if_alone_timeout_milliseconds': 200,
        'basic.to_if_held_down_threshold_milliseconds': 200,
      },
    },
  ];
}

/**
 * Generates the Karabiner events for a double-tap-to-toggle behaviour.
 *
 * @param args - Arguments for the double tap to manipupators
 * @param args.key - The key to be double-tapped
 * @param args.to - The events emitted on the second tap
 * @param args.globalVar - The variable name used to track the pressed state
 * @param args.type - The type of key, either 'normal' or 'vendor'
 *
 * @returns Karabiner event representation of the double tap to manipupators
 */
export function doubleTapToManipupators(args: {
  key: string;
  to: unknown;
  globalVar: string;
  type?: 'normal' | 'vendor';
}) {
  const { key, to, globalVar, type = 'normal' } = args;
  const keyType =
    type === 'normal' ? 'key_code' : 'apple_vendor_top_case_key_code';

  return [
    {
      type: 'basic',
      conditions: [{ name: globalVar, type: 'variable_if', value: true }],
      from: { [keyType]: key, modifiers: { optional: ['any'] } },
      to: [{ [keyType]: key }],
      to_if_alone: to,
      to_after_key_up: [{ set_variable: { name: globalVar, value: false } }],
    },
    {
      type: 'basic',
      from: { [keyType]: key, modifiers: { optional: ['any'] } },
      to: [{ [keyType]: key }],
      to_if_alone: [{ set_variable: { name: globalVar, value: true } }],
      to_delayed_action: {
        to_if_canceled: [{ set_variable: { name: globalVar, value: false } }],
        to_if_invoked: [{ set_variable: { name: globalVar, value: false } }],
      },
      parameters: {
        'basic.to_if_alone_timeout_milliseconds': 250,
        'basic.to_delayed_action_delay_milliseconds': 500,
      },
    },
  ];
}
