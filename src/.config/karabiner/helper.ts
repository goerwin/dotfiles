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
