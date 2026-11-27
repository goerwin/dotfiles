// Builds build/skills from src/.agents/skills, replacing each
// `<!-- include: name.md -->` line with src/.agents/skills/shared/name.md.

import {
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const sourcesDir = join(root, 'src/.agents/skills');
const sharedDir = join(sourcesDir, 'shared');
const outputDir = join(root, 'build/skills');
const includePattern = /^<!-- include: (\S+) -->$/gm;

function listFiles(dir) {
  return readdirSync(dir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name !== '.DS_Store')
    .map((entry) => relative(dir, join(entry.parentPath, entry.name)));
}

function render(text) {
  return text.replace(includePattern, (_, name) => {
    const shared = readFileSync(join(sharedDir, name), 'utf8').trim();
    if (shared.includes('<!-- include: ')) {
      throw new Error(`${name} has an include; shared files can't nest`);
    }
    return shared;
  });
}

rmSync(outputDir, { recursive: true, force: true });
for (const skill of readdirSync(sourcesDir, { withFileTypes: true })) {
  if (!skill.isDirectory() || skill.name === 'shared') continue;
  const skillDir = join(sourcesDir, skill.name);
  for (const file of listFiles(skillDir)) {
    const text = readFileSync(join(skillDir, file), 'utf8');
    const destination = join(outputDir, skill.name, file);
    mkdirSync(dirname(destination), { recursive: true });
    writeFileSync(destination, file === 'SKILL.md' ? render(text) : text);
  }
}
