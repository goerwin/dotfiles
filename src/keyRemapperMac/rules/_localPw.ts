/**
 *  This file is used to generate the _localPw.json file (Alt + V types LOCAL_PW).
 *  You can run it via node (eg. node _localPw.ts > _localPw.json)
 *  Use the .env at root to set the LOCAL_PW
 */

// @ts-expect-error - no definitions
import { fileURLToPath } from 'node:url';

try {
  // @ts-expect-error - process.loadEnvFile is not defined in the type definitions
  process.loadEnvFile(fileURLToPath(import.meta.resolve('../../../.env')));
} catch (error: unknown) {
  console.warn(
    "Warning: couldn't load .env file, perhaps it doesn't exist:",
    (error as Error)?.message,
  );
}

// @ts-expect-error - process.env is not defined in the type definitions
const LOCAL_PW: string | undefined = process.env.LOCAL_PW;

function getKeyEventsFromLetter(letter: string) {
  if (/[a-z]/.test(letter)) return letter.toUpperCase();
  if (/[0-9]/.test(letter)) return letter;
  if (/[A-Z]/.test(letter)) return `ShiftL+${letter}`;
  if (letter === '$') return 'ShiftL+4';

  throw new Error(`LOCAL_PW has an unsupported character: ${letter}`);
}

const rules = LOCAL_PW
  ? [
      {
        from: ['V'],
        modifiers: ['AltL'],
        to: Array.from(LOCAL_PW).map(getKeyEventsFromLetter).join(' '),
      },
    ]
  : [];

console.log(JSON.stringify(rules, null, 2));
