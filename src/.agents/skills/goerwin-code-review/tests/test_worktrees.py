import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from goerwin_tools import herdr_adapter, runtime, worktrees

ROOT = SKILL.parents[3]
COMMAND = ROOT / "src/.agents/shared/goerwin-wts"


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="goerwin-wts-")
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo with spaces $(literal)"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Worktree Tests")
        self.git("config", "user.email", "tests@example.invalid")
        (self.repo / "file").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.remote = self.root / "remote.git"
        subprocess.run(["git", "clone", "--bare", str(self.repo), str(self.remote)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(self.remote))
        self.git("fetch", "origin")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        executable = self.bin / "wt"
        executable.write_text(f"#!{sys.executable}\n" + textwrap.dedent('''
            import json, os, subprocess, sys
            from pathlib import Path
            args = sys.argv[1:]
            with open(os.environ["WTS_TEST_LOG"], "a") as log:
                log.write(json.dumps(args) + "\\n")
            repo = args[args.index("-C") + 1]
            selector = args[args.index("switch") + 1]
            create = selector == "--create"
            branch = args[args.index("--create") + 1] if create else selector
            base = args[args.index("--base") + 1] if "--base" in args else None
            if branch.startswith("https://"):
                branch = "pr-topic"
                create, base = True, "main"
            path = Path(os.environ["WTS_TEST_ROOT"]) / branch.replace("/", "__")
            command = ["git", "-C", repo, "worktree", "add"]
            if create:
                command += ["-b", branch, str(path), base]
            elif branch.startswith("origin/"):
                command += ["--track", "-b", branch.removeprefix("origin/"), str(path), branch]
            else:
                command += [str(path), branch]
            subprocess.run(command, check=True, capture_output=True)
            print(json.dumps({"path": str(path)}))
        ''').lstrip())
        executable.chmod(0o755)
        self.log = self.root / "wt.jsonl"
        self.config = self.root / "config.json"
        self.environment = patch.dict(os.environ, {
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "WTS_TEST_ROOT": str(self.root / "worktrees"), "WTS_TEST_LOG": str(self.log),
            "HOME": str(self.root), "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C.UTF-8",
        }, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or self.repo), *args],
                              check=True, capture_output=True, text=True).stdout.strip()

    def switch(self, target, base=None, cwd=None):
        return worktrees.switch(target, str(cwd or self.repo), base, self.config, focus=False)

    def pr(self, **overrides):
        return {"url": "https://github.com/example/project/pull/123", "number": 123,
                "headRefName": "pr-topic", "isCrossRepository": False, **overrides}

    def test_new_branch_fetches_remote_default_and_preserves_source_edits(self):
        upstream = self.root / "upstream"
        self.git("clone", str(self.remote), str(upstream))
        self.git("config", "user.name", "Tests", cwd=upstream)
        self.git("config", "user.email", "tests@example.invalid", cwd=upstream)
        (upstream / "new-file").write_text("remote change")
        self.git("add", ".", cwd=upstream)
        self.git("commit", "-m", "remote change", cwd=upstream)
        self.git("push", "origin", "main", cwd=upstream)
        expected = self.git("rev-parse", "HEAD", cwd=upstream)
        (self.repo / "file").write_text("personal work\n")
        result = self.switch("feat/component")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=result["path"]), expected)
        self.assertEqual((self.repo / "file").read_text(), "personal work\n")
        self.assertEqual(self.git("branch", "--show-current"), "main")

    def test_reuse_preserves_dirty_tree_and_ignores_creation_base(self):
        first = self.switch("feat/component", "main")
        (Path(first["path"]) / "file").write_text("dirty work\n")
        self.log.unlink()
        result = self.switch("feat/component", "missing/base")
        self.assertEqual(result["path"], first["path"])
        self.assertTrue(result["reused"])
        self.assertFalse(self.log.exists())
        self.assertEqual((Path(result["path"]) / "file").read_text(), "dirty work\n")

    def test_existing_branch_without_worktree_keeps_its_commit(self):
        self.git("branch", "feature", "main")
        result = self.switch("feature", "missing/base")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=result["path"]), self.base)
        self.assertNotIn("--create", json.loads(self.log.read_text()))

    def test_explicit_local_base_does_not_fetch(self):
        self.git("remote", "set-url", "origin", str(self.root / "missing.git"))
        result = self.switch("feature", "main")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=result["path"]), self.base)

    def test_remote_only_branches_get_local_tracking_worktrees(self):
        for index, qualified in enumerate((False, True)):
            branch = f"remote-topic-{index}"
            self.git("push", "origin", f"main:{branch}")
            self.git("fetch", "origin")
            result = self.switch(f"origin/{branch}" if qualified else branch)
            self.assertEqual(result["branch"], branch)
            self.assertEqual(self.git("branch", "--show-current", cwd=result["path"]), branch)
            self.assertEqual(self.git("config", f"branch.{branch}.remote"), "origin")

    def test_failed_fetch_creates_nothing(self):
        self.git("remote", "set-url", "origin", str(self.root / "missing.git"))
        with self.assertRaises(runtime.CommandError):
            self.switch("feature")
        self.assertFalse(self.log.exists())
        self.assertEqual(self.git("branch", "--list", "feature"), "")

    def test_number_reuses_existing_pr_branch_without_updating_it(self):
        existing = self.switch("pr-topic", "main")
        self.git("remote", "set-url", "origin", "https://github.com/example/project.git")
        self.log.unlink()
        with patch.object(worktrees, "github", return_value=self.pr()):
            result = self.switch("123")
        self.assertEqual(result["path"], existing["path"])
        self.assertFalse(self.log.exists())

    def test_registered_url_works_outside_any_repository(self):
        self.git("remote", "set-url", "origin", "https://github.com/example/project.git")
        runtime.register_checkout(self.repo, self.config)
        with patch.object(worktrees, "github", return_value=self.pr()):
            result = self.switch(self.pr()["url"], cwd=self.root)
        self.assertEqual(result["branch"], "pr-topic")
        self.assertEqual(self.git("config", "branch.pr-topic.goerwin-pr-url"), self.pr()["url"])
        self.assertIn(self.pr()["url"], json.loads(self.log.read_text()))

    def test_unknown_repository_does_not_clone_or_create(self):
        with self.assertRaisesRegex(runtime.CommandError, "register"):
            self.switch("https://github.com/unknown/project/pull/123", cwd=self.root)
        self.assertFalse(self.log.exists())

    def test_fork_branch_conflict_does_not_reuse_an_unrelated_local_branch(self):
        self.git("branch", "pr-topic")
        self.git("remote", "set-url", "origin", "https://github.com/example/project.git")
        pr = self.pr(isCrossRepository=True, headRepository={"nameWithOwner": "contributor/project"})
        with patch.object(worktrees, "github", return_value=pr):
            with self.assertRaisesRegex(runtime.CommandError, "conflict"):
                self.switch("123")
        self.assertFalse(self.log.exists())

    def test_cli_prints_only_the_path(self):
        result = subprocess.run([sys.executable, str(COMMAND), "feature", "main", "--no-focus"],
                                cwd=self.repo, check=True, capture_output=True, text=True)
        self.assertTrue(Path(result.stdout.strip()).is_dir())
        self.assertEqual(len(result.stdout.splitlines()), 1)

    def test_account_override_does_not_switch_global_gh_account(self):
        response = subprocess.CompletedProcess([], 0, "test-token", "")
        with patch.object(runtime, "run", return_value=response) as run:
            env = runtime.github_environment("chosen-user", "github.com")
        self.assertEqual(run.call_args.args[0], ["gh", "auth", "token", "--hostname", "github.com", "--user", "chosen-user"])
        self.assertEqual(env["GH_TOKEN"], "test-token")
        self.assertFalse("GH_TOKEN" in run.call_args.kwargs["env"])


class FocusTests(unittest.TestCase):
    def test_focus_reuses_existing_local_space_and_active_tab(self):
        state = {"spaces": [{"id": "space", "folder": "/tmp/worktree", "machine": None,
                              "tabs": [{"id": "tab", "active": True, "terminals": [{"terminal": "terminal"}]}]}]}
        with patch.object(herdr_adapter, "snapshot", return_value=state):
            with patch.object(herdr_adapter, "command", return_value={}) as command:
                with patch.object(herdr_adapter.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")):
                    result = worktrees.focus_worktree("/tmp/worktree", "feature")
        self.assertTrue(result["available"])
        self.assertEqual([call.args[0] for call in command.call_args_list], [
            ["do", "tab.select", "--id", "tab"], ["do", "pane.focus", "--terminal", "terminal"],
        ])

    def test_unavailable_herdr_does_not_block_or_launch_it(self):
        with patch.object(herdr_adapter, "snapshot", side_effect=herdr_adapter.AdapterError("unavailable")):
            with patch.object(herdr_adapter, "command") as command:
                result = worktrees.focus_worktree("/tmp/worktree", "feature")
        self.assertFalse(result["available"])
        command.assert_not_called()


class InstallationTests(unittest.TestCase):
    def test_install_skills_installs_one_shared_copy_and_working_links(self):
        if not shutil.which("zsh") or not shutil.which("rsync"):
            self.skipTest("zsh and rsync are required for installer checks")
        with tempfile.TemporaryDirectory(prefix="install-skills-") as tmp:
            home = Path(tmp).resolve()
            env = dict(os.environ, GOERWIN_SKILLS_HOME=tmp, HOME=tmp, PYTHONDONTWRITEBYTECODE="1")
            subprocess.run(["zsh", "bin/install-skills.zsh"], cwd=ROOT, env=env, check=True, capture_output=True)
            command = home / ".local/bin/goerwin-wts"
            self.assertTrue(command.is_symlink())
            subprocess.run([str(command), "--help"], check=True, env=env, capture_output=True)
            for skill, args in (("goerwin-code-review", ["review_pr.py", "presets"]),
                               ("goerwin-receiving-code-review", ["receiving.py", "--help"])):
                scripts = home / ".agents/skills" / skill / "scripts"
                self.assertTrue((scripts / "goerwin_tools").is_symlink())
                self.assertEqual((scripts / "goerwin_tools").resolve(), home / ".agents/shared/goerwin_tools")
                subprocess.run([sys.executable, str(scripts / args[0]), *args[1:]], check=True, env=env, capture_output=True)
