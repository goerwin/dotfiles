import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_worktrees import ROOT


class InstallationTests(unittest.TestCase):
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

    def test_installed_command_finds_its_reference(self):
        self.install()
        self.install()
        result = subprocess.run([str(self.bin / "goerwin-wt"), "--help"], env=self.env, check=True,
                                capture_output=True, text=True)
        reference = self.root / ".local/lib/goerwin_tools/README.md"
        self.assertIn(str(reference), result.stdout.replace("\n", ""))
        self.assertTrue(reference.is_file())

    def test_unrelated_command_is_not_replaced(self):
        foreign = self.root / "foreign"
        foreign.write_text("keep this")
        (self.bin / "goerwin-wt").symlink_to(foreign)
        result = self.install(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrelated", result.stderr)
        self.assertEqual((self.bin / "goerwin-wt").resolve(), foreign)

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


if __name__ == "__main__":
    unittest.main()
