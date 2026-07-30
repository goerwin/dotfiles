/**
 * Static pieces of the main profile: device-specific simple modifications,
 * function-key passthrough, and global simple modifications.
 */

export const devices = [
  {
    identifiers: { is_keyboard: true, product_id: 32, vendor_id: 9494 },
    simple_modifications: [
      {
        from: { key_code: 'grave_accent_and_tilde' },
        to: [{ key_code: 'grave_accent_and_tilde' }],
      },
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
    ],
  },

  // G10 Control
  {
    identifiers: {
      is_pointing_device: true,
      product_id: 4133,
      vendor_id: 6421,
    },
    ignore: false,
    pointing_motion_wheels_multiplier: 0.5,
    pointing_motion_xy_multiplier: 0.5,
  },
];

export const fnFunctionKeys = [
  { from: { key_code: 'f1' }, to: [{ key_code: 'f1' }] },
  { from: { key_code: 'f2' }, to: [{ key_code: 'f2' }] },
  { from: { key_code: 'f3' }, to: [{ key_code: 'f3' }] },
  { from: { key_code: 'f4' }, to: [{ key_code: 'f4' }] },
  { from: { key_code: 'f5' }, to: [{ key_code: 'f5' }] },
  { from: { key_code: 'f7' }, to: [{ key_code: 'f7' }] },
  { from: { key_code: 'f8' }, to: [{ key_code: 'f8' }] },
  { from: { key_code: 'f9' }, to: [{ key_code: 'f9' }] },
  { from: { key_code: 'f10' }, to: [{ key_code: 'f10' }] },
  { from: { key_code: 'f11' }, to: [{ key_code: 'f11' }] },
  { from: { key_code: 'f12' }, to: [{ key_code: 'f12' }] },
];

export const simpleModifications = [
  { from: { key_code: 'caps_lock' }, to: [{ key_code: 'f18' }] },
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
  {
    from: { key_code: 'right_option' },
    to: [{ key_code: 'left_option' }],
  },
  { from: { key_code: 'right_shift' }, to: [{ key_code: 'left_shift' }] },
];
