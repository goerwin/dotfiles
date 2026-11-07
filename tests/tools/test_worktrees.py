import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "src/.local/lib"
BIN = ROOT / "src/.local/bin"
sys.path.insert(0, str(LIB))
from goerwin_tools import herdr_adapter, runtime, worktrees

COMMAND = BIN / "goerwin-wt"


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="goerwin-wt-")
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
            if "list" in args:
                output = subprocess.run(["git", "-C", repo, "worktree", "list", "--porcelain"], check=True, capture_output=True, text=True).stdout
                items = []
                for index, block in enumerate(output.strip().split("\\n\\n")):
                    fields = dict(line.partition(" ")[::2] for line in block.splitlines())
                    path = fields["worktree"]
                    dirty = subprocess.run(["git", "-C", path, "status", "--porcelain"], capture_output=True, text=True).stdout
                    tree = {"path": path, "main": index == 0, "changes": {"modified": bool(dirty)}}
                    if "locked" in fields:
                        tree["locked"] = {"reason": fields["locked"]}
                    items.append({"branch": fields.get("branch", "").removeprefix("refs/heads/") or None, "worktree": tree})
                print(json.dumps({"schema": 2, "repo": {"default_branch": "main"}, "collected": {}, "items": items}))
                sys.exit(0)
            if "remove" in args:
                if os.environ.get("WTS_TEST_REMOVE_FAIL"):
                    sys.exit("pre-remove hook failed")
                target = args[args.index("remove") + 1]
                subprocess.run(["git", "-C", repo, "worktree", "remove", *(["--force"] if "--force" in args else []), target], check=True, capture_output=True)
                print(json.dumps({"kind": "worktree", "path": target, "branch_outcome": "not_attempted"}))
                sys.exit(0)
            selector = args[args.index("switch") + 1]
            create = selector == "--create"
            branch = args[args.index("--create") + 1] if create else selector
            base = args[args.index("--base") + 1] if "--base" in args else None
            if branch.startswith("https://"):
                branch = "pr-topic"
                create, base = True, "main"
            path = Path(os.environ["WTS_TEST_ROOT"]) / branch.replace("/", "__")
            command = ["git", "-C", repo, "worktree", "add"]
            command += ["-b", branch, str(path), base] if create else [str(path), branch]
            subprocess.run(command, check=True, capture_output=True)
            print(json.dumps({"path": str(path)}))
        ''').lstrip())
        executable.chmod(0o755)
        self.log = self.root / "wt.jsonl"
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
        return worktrees.switch(target, str(cwd or self.repo), base, focus=False)

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

    def add_remote(self, name):
        bare = self.root / f"{name}.git"
        subprocess.run(["git", "clone", "--bare", str(self.repo), str(bare)], check=True, capture_output=True)
        self.git("remote", "add", name, str(bare))
        return bare

    def push_elsewhere(self, remote, branch):
        clone = self.root / f"clone-{branch}"
        subprocess.run(["git", "clone", str(remote), str(clone)], check=True, capture_output=True)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "--allow-empty", "-m", branch, cwd=clone)
        self.git("push", "origin", f"HEAD:{branch}", cwd=clone)
        return self.git("rev-parse", "HEAD", cwd=clone)

    def test_branch_on_several_remotes_tracks_origin_or_the_explicit_remote(self):
        self.add_remote("upstream")
        for name in ("shared", "chosen"):
            self.git("push", "origin", f"main:{name}")
            self.git("push", "upstream", f"main:{name}")
        self.git("fetch", "--all")
        self.switch("shared")
        self.assertEqual(self.git("config", "branch.shared.remote"), "origin")
        result = self.switch("upstream/chosen")
        self.assertEqual(result["branch"], "chosen")
        self.assertEqual(self.git("config", "branch.chosen.remote"), "upstream")

    def test_unfetched_remote_branch_is_tracked_not_recreated(self):
        expected = self.push_elsewhere(self.remote, "teammate-topic")
        result = self.switch("teammate-topic")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=result["path"]), expected)
        self.assertEqual(self.git("config", "branch.teammate-topic.remote"), "origin")

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

    def test_pr_url_works_from_its_checkout(self):
        self.git("remote", "set-url", "origin", "https://github.com/example/project.git")
        with patch.object(worktrees, "github", return_value=self.pr()):
            result = self.switch(self.pr()["url"])
        self.assertEqual(result["branch"], "pr-topic")
        self.assertEqual(self.git("config", "branch.pr-topic.goerwin-pr-url"), self.pr()["url"])
        self.assertIn(self.pr()["url"], json.loads(self.log.read_text()))

    def test_other_repository_pr_does_not_clone_or_create(self):
        for cwd in (self.root, self.repo):
            with self.assertRaisesRegex(runtime.CommandError, "never cloned"):
                self.switch("https://github.com/unknown/project/pull/123", cwd=cwd)
        self.assertFalse(self.log.exists())

    def test_fork_branch_conflict_does_not_reuse_an_unrelated_local_branch(self):
        self.git("branch", "pr-topic")
        self.git("remote", "set-url", "origin", "https://github.com/example/project.git")
        pr = self.pr(isCrossRepository=True, headRepository={"nameWithOwner": "contributor/project"})
        with patch.object(worktrees, "github", return_value=pr):
            with self.assertRaisesRegex(runtime.CommandError, "conflict"):
                self.switch("123")
        self.assertFalse(self.log.exists())

    def test_cli_streams_worktrunk_progress_to_stderr(self):
        wt = self.bin / "wt"
        wt.write_text(wt.read_text().replace(
            'subprocess.run(command, check=True, capture_output=True)',
            'print("SETUP PROGRESS", file=sys.stderr, flush=True)\nsubprocess.run(command, check=True, capture_output=True)'))
        result = subprocess.run([sys.executable, str(COMMAND), "switch", "feature", "main"],
                                cwd=self.repo, check=True, capture_output=True, text=True)
        self.assertIn("SETUP PROGRESS", result.stderr)
        self.assertNotIn("SETUP PROGRESS", result.stdout)

    def test_cli_prints_only_the_path(self):
        result = subprocess.run([sys.executable, str(COMMAND), "switch", "feature", "main"],
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

    def test_no_focus_opens_a_tab_and_reselects_the_previous_one(self):
        state = {"spaces": [{"id": "current", "folder": "/tmp/other", "machine": None, "active": True,
                             "tabs": [{"id": "mine", "active": True}]}]}
        with patch.object(herdr_adapter, "snapshot", return_value=state):
            with patch.object(herdr_adapter, "command", return_value={"tab": "new"}) as command:
                with patch.object(herdr_adapter.subprocess, "run") as raised:
                    result = worktrees.focus_worktree("/tmp/worktree", "feature", focus=False)
        calls = [call.args[0][:2] for call in command.call_args_list]
        self.assertEqual(calls, [["do", "space.new"], ["do", "tab.select"]])
        self.assertEqual(command.call_args_list[1].args[0][-1], "mine")
        raised.assert_not_called()
        self.assertEqual(result["tab"], "new")

    def test_no_focus_leaves_an_existing_tab_alone(self):
        state = {"spaces": [{"id": "space", "folder": "/tmp/worktree", "machine": None,
                             "tabs": [{"id": "tab", "active": True}]}]}
        with patch.object(herdr_adapter, "snapshot", return_value=state):
            with patch.object(herdr_adapter, "command") as command:
                worktrees.focus_worktree("/tmp/worktree", "feature", focus=False)
        command.assert_not_called()

    def test_unavailable_herdr_does_not_block_or_launch_it(self):
        with patch.object(herdr_adapter, "snapshot", side_effect=herdr_adapter.AdapterError("unavailable")):
            with patch.object(herdr_adapter, "command") as command:
                result = worktrees.focus_worktree("/tmp/worktree", "feature")
        self.assertFalse(result["available"])
        command.assert_not_called()

    def test_review_tab_matches_exact_folder_and_focus_warning_does_not_relaunch(self):
        calls = []
        def fake(args):
            calls.append(args)
            if args[:2] == ["do", "pane.focus"]:
                raise herdr_adapter.AdapterError("focus unavailable")
            return {"space": "sp-existing", "tab": "tab-new", "terminal": "t-new"}
        with patch.object(herdr_adapter, "command", side_effect=fake):
            with patch.object(herdr_adapter.subprocess, "run") as raised:
                raised.return_value.returncode = 0
                result = herdr_adapter.open_review(
                    "/tmp/review-space", "Review", ["codex", "--no-daemon"], "Review this",
                    {"spaces": [
                        {"id": "sp-wrong", "folder": "/tmp", "machine": None},
                        {"id": "sp-existing", "folder": "/tmp/review-space", "machine": None},
                    ]},
                )
        create = calls[0]
        self.assertEqual(create[:4], ["do", "tab.new", "--space", "sp-existing"])
        self.assertEqual(json.loads(create[create.index("--argv") + 1]), ["codex", "--no-daemon"])
        self.assertEqual(create[create.index("--task") + 1], "Review this")
        self.assertEqual(len([item for item in calls if item[:2] == ["do", "tab.new"]]), 1)
        self.assertEqual(result["warnings"], ["focus unavailable"])

    def test_missing_local_space_creates_a_new_worktree_space(self):
        with patch.object(herdr_adapter, "command", return_value={"space": "sp", "tab": "tab"}) as command:
            with patch.object(herdr_adapter.subprocess, "run") as raised:
                raised.return_value.returncode = 0
                herdr_adapter.open_review(
                    "/tmp/review-space", "Review", ["claude"], "Review this",
                    {"spaces": [{"id": "remote", "folder": "/tmp/review-space", "machine": "server"}]},
                )
        self.assertEqual(command.call_args_list[0].args[0][:3], ["do", "space.new", "--tab"])

    def test_raise_timeout_is_a_warning(self):
        with patch.object(herdr_adapter, "snapshot", return_value={"spaces": []}):
            with patch.object(herdr_adapter, "command", return_value={"tab": "t"}):
                with patch.object(herdr_adapter.subprocess, "run", side_effect=herdr_adapter.subprocess.TimeoutExpired("herdr-app", 15)):
                    result = worktrees.focus_worktree("/tmp/worktree", "feature")
        self.assertTrue(result["available"])
        self.assertEqual(len(result["warnings"]), 1)
