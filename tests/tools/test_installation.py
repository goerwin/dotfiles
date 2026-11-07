import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_worktrees import ROOT

RETIRED_SKILLS = ("goerwin-code-review", "goerwin-receiving-code-review", "goerwin-review-loop",
                  "goerwin-architecture-review")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tool-installation-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.bin = self.root / ".local/bin"
        self.bin.mkdir(parents=True)
        self.env = dict(os.environ, GOERWIN_TOOLS_HOME=str(self.root), GOERWIN_SKILLS_HOME=str(self.root),
                        PYTHONDONTWRITEBYTECODE="1")

    def install(self, name="tools", check=True):
        return subprocess.run(["zsh", str(ROOT / f"bin/install-{name}.zsh"), "--no-update"],
                              env=self.env, cwd=ROOT, text=True, capture_output=True, check=check)

    def test_known_legacy_links_migrate_and_extra_files_are_preserved(self):
        legacy = self.root / ".agents/shared"
        legacy.mkdir(parents=True)
        (legacy / "personal-extra").write_text("keep this")
        for command in ("goerwin-wts", "goerwin-review"):
            (legacy / command).write_text("old helper")
            (self.bin / command).symlink_to(f"../../.agents/shared/{command}")
        self.install()
        self.assertFalse((self.bin / "goerwin-wts").is_symlink())
        self.assertFalse((self.bin / "goerwin-review").is_symlink())
        self.install("skills")
        self.assertFalse(legacy.exists())
        backups = list((self.root / ".local/state/goerwin-tools").glob("legacy-shared.*/shared/personal-extra"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "keep this")
        self.install()
        self.assertFalse((self.bin / "goerwin-wt").is_symlink())
        subprocess.run([str(self.bin / "goerwin-wt"), "--help"], env=self.env, check=True, capture_output=True)

    def test_unrelated_commands_are_not_replaced(self):
        foreign = self.root / "foreign"
        foreign.write_text("keep this")
        (self.bin / "goerwin-wt").symlink_to(foreign)
        result = self.install(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrelated", result.stderr)
        self.assertEqual((self.bin / "goerwin-wt").resolve(), foreign)
        (self.bin / "goerwin-wt").unlink()
        (self.bin / "goerwin-review").symlink_to(foreign)
        result = self.install()
        self.assertIn("Left unrelated goerwin-review", result.stderr)
        self.assertEqual((self.bin / "goerwin-review").resolve(), foreign)

    def test_managed_review_command_is_removed(self):
        (self.bin / "goerwin-review").write_text("#!/usr/bin/env python3\n# goerwin-tools entry point\n")
        self.install()
        self.assertFalse((self.bin / "goerwin-review").exists())

    def test_unrelated_legacy_name_is_left_untouched(self):
        (self.bin / "goerwin-wts").write_text("personal unrelated command")
        self.install()
        self.assertEqual((self.bin / "goerwin-wts").read_text(), "personal unrelated command")

    def test_install_skills_installs_working_review_skill_and_keeps_direct_links(self):
        direct = self.root / ".codex/skills/goerwin-handoff"
        direct.parent.mkdir(parents=True)
        direct.symlink_to(ROOT / "src/.agents/skills/goerwin-handoff")
        self.install("skills")
        self.assertEqual(direct.resolve(), ROOT / "src/.agents/skills/goerwin-handoff")
        self.assertFalse(list(self.root.glob(".agents/**/tests")))
        for skill in ("goerwin-handoff", "goerwin-review"):
            scripts = self.root / ".agents/skills" / skill / "scripts"
            self.assertEqual((scripts / "goerwin_tools").resolve(), self.root / ".local/lib/goerwin_tools")
        self.assertEqual((self.root / ".codex/skills/goerwin-review").resolve(),
                         self.root / ".agents/skills/goerwin-review")
        scripts = self.root / ".agents/skills/goerwin-review/scripts"
        for args in (["review.py", "presets"], ["receiving.py", "--help"], ["review_loop.py", "--help"]):
            subprocess.run([sys.executable, str(scripts / args[0]), *args[1:]], check=True, env=self.env,
                           capture_output=True)

    def test_retired_skills_move_to_a_backup_and_unrelated_entries_stay(self):
        skills = self.root / ".agents/skills"
        for skill in RETIRED_SKILLS:
            (skills / skill).mkdir(parents=True)
            (skills / skill / "SKILL.md").write_text(f"---\nname: {skill}\n---\n")
            for harness in (".claude", ".codex"):
                link = self.root / harness / "skills" / skill
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(f"../../.agents/skills/{skill}")
        (self.root / ".codex/skills/goerwin-review-loop").unlink()
        (self.root / ".codex/skills/goerwin-review-loop").symlink_to(self.root / "personal-loop")
        (skills / "goerwin-architecture-review/SKILL.md").write_text("---\nname: my-architecture\n---\n")
        result = self.install("skills")
        retired, kept = RETIRED_SKILLS[:3], "goerwin-architecture-review"
        backup = next((self.root / ".local/state/goerwin-tools").glob("retired-skills.*"))
        self.assertEqual(sorted(path.name for path in backup.iterdir()), sorted(retired))
        for skill in retired:
            self.assertFalse((skills / skill).exists())
            self.assertFalse((self.root / ".claude/skills" / skill).is_symlink())
        self.assertEqual((self.root / ".codex/skills/goerwin-review-loop").resolve(), self.root / "personal-loop")
        self.assertEqual((skills / kept / "SKILL.md").read_text(), "---\nname: my-architecture\n---\n")
        self.assertEqual((self.root / ".claude/skills" / kept).resolve(), skills / kept)
        self.assertIn(f"Left {skills / kept} untouched", result.stderr)
        self.assertTrue((self.root / ".claude/skills/goerwin-review").is_symlink())


if __name__ == "__main__":
    unittest.main()
