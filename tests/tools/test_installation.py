import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_worktrees import ROOT


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
        old_scripts = self.root / ".agents/skills/goerwin-code-review/scripts"
        old_scripts.mkdir(parents=True)
        (legacy / "goerwin_tools").mkdir()
        (old_scripts / "goerwin_tools").symlink_to("../../../shared/goerwin_tools")
        self.install()
        self.assertFalse((self.bin / "goerwin-wts").is_symlink())
        self.assertTrue((old_scripts / "goerwin_tools").is_dir())
        self.install("skills")
        self.assertFalse(legacy.exists())
        backups = list((self.root / ".local/state/goerwin-tools").glob("legacy-shared.*/shared/personal-extra"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "keep this")
        self.install()
        for command in ("goerwin-wt", "goerwin-review"):
            self.assertFalse((self.bin / command).is_symlink())
            subprocess.run([str(self.bin / command), "--help"], env=self.env, check=True, capture_output=True)

    def test_unrelated_command_is_not_replaced(self):
        foreign = self.root / "foreign-review"
        foreign.write_text("keep this")
        (self.bin / "goerwin-review").symlink_to(foreign)
        result = self.install(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrelated", result.stderr)
        self.assertEqual((self.bin / "goerwin-review").resolve(), foreign)
        self.assertFalse((self.bin / "goerwin-wt").exists())

    def test_unrelated_legacy_name_is_left_untouched(self):
        (self.bin / "goerwin-wts").write_text("personal unrelated command")
        self.install()
        self.assertEqual((self.bin / "goerwin-wts").read_text(), "personal unrelated command")

    def test_codex_direct_source_link_is_preserved_and_other_links_work(self):
        direct = self.root / ".codex/skills/goerwin-handoff"
        direct.parent.mkdir(parents=True)
        direct.symlink_to(ROOT / "src/.agents/skills/goerwin-handoff")
        self.install("skills")
        self.assertEqual(direct.resolve(), ROOT / "src/.agents/skills/goerwin-handoff")
        installed = self.root / ".agents/skills/goerwin-handoff"
        self.assertEqual((installed / "scripts/goerwin_tools").resolve(), self.root / ".local/lib/goerwin_tools")
        self.assertEqual((self.root / ".codex/skills/goerwin-code-review").resolve(),
                         self.root / ".agents/skills/goerwin-code-review")
