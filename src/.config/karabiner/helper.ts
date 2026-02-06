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
