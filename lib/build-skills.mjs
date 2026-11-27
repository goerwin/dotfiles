// Builds src/.agents/skills from src/.agents/skill-sources.
// --check: exit 1 when the built skills are out of date.

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
const sourcesDir = join(root, 'src/.agents/skill-sources');
const sharedDir = join(sourcesDir, 'shared');
const outputDir = join(root, 'src/.agents/skills');
const includePattern = /^<!-- include: (\S+) -->$/gm;

function listFiles(dir) {
  return readdirSync(dir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name !== '.DS_Store')
    .map((entry) => relative(dir, join(entry.parentPath, entry.name)))
    .sort();
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

function build() {
  const files = new Map();
  for (const skill of readdirSync(sourcesDir, { withFileTypes: true })) {
    if (!skill.isDirectory() || skill.name === 'shared') continue;
    const skillDir = join(sourcesDir, skill.name);
    for (const file of listFiles(skillDir)) {
      const text = readFileSync(join(skillDir, file), 'utf8');
      files.set(
        join(skill.name, file),
        file === 'SKILL.md' ? render(text) : text,
      );
    }
  }
  return files;
}

const files = build();

if (process.argv.includes('--check')) {
  const built = listFiles(outputDir);
  const stale = [
    ...built.filter((file) => !files.has(file)),
    ...[...files].flatMap(([file, text]) => {
      try {
        return readFileSync(join(outputDir, file), 'utf8') === text
          ? []
          : [file];
      } catch {
        return [file];
      }
    }),
  ];
  if (stale.length) {
    console.error(
      `Built skills are out of date; run make build-skills:\n  ${stale.join('\n  ')}`,
    );
    process.exit(1);
  }
} else {
  rmSync(outputDir, { recursive: true, force: true });
  for (const [file, text] of files) {
    mkdirSync(dirname(join(outputDir, file)), { recursive: true });
    writeFileSync(join(outputDir, file), text);
  }
  console.log(`Built ${files.size} files into ${relative(root, outputDir)}`);
}
