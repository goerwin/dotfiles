import datetime as dt
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

SHARED = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SHARED))
from goerwin_tools import herdr_adapter, review_store as store, runtime, worktrees

ROOT = SHARED.parents[2]
COMMAND = SHARED / "goerwin-wts"


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
            command += ["-b", branch, str(path), base] if create else [str(path), branch]
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


    def test_save_command_archives_a_snapshot_review(self):
        body = self.root / "body.md"
        body.write_text("# Architecture\n\n### F1: Duplicate helper\n`a.py:1` · suggestion\n")
        env = dict(os.environ, GOERWIN_CODE_REVIEWS_DIR=str(self.root / "archive"))
        result = subprocess.run([
            sys.executable, str(SHARED / "goerwin-review"), "save", "--body", str(body),
            "--skill", "codebase-architecture-review", "--harness", "claude",
            "--model", "claude-opus-5-5", "--effort", "high", "--scope", "src", "-C", str(self.repo),
        ], env=env, check=True, capture_output=True, text=True)
        saved = store.read_report(json.loads(result.stdout)["report"])
        meta = saved["metadata"]
        self.assertEqual((meta["skill"], meta["scope"], meta["base_sha"]), ("codebase-architecture-review", "src", None))
        self.assertEqual((meta["head_sha"], meta["finding_ids"]), (self.base, ["F1"]))
        body.write_text("loose notes without headings")
        failed = subprocess.run([sys.executable, str(SHARED / "goerwin-review"), "save", "--body", str(body),
                                 "--skill", "x", "--harness", "claude", "--model", "m", "--effort", "e",
                                 "-C", str(self.repo)], env=env, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(len(list((self.root / "archive").glob("*/*.md"))), 1)

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


class ArchiveTests(unittest.TestCase):
    def test_daily_index_per_project_and_owner_on_name_clash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            day = dt.datetime(2026, 11, 11, 9, tzinfo=dt.timezone.utc)
            target = {"source_root": "/x/antares", "repository": "github.com/godaddy/antares",
                      "kind": "pr", "pr_number": 123, "title": "Pagination"}
            first = store.report_path(root, target, day)
            second = store.report_path(root, {**target, "kind": "snapshot", "title": "src"}, day)
            self.assertEqual(first.relative_to(root).as_posix(), "antares/2026-11-11-01-pr-123-pagination.md")
            self.assertEqual(second.name, "2026-11-11-02-src.md")
            first.unlink()
            self.assertEqual(store.report_path(root, target, day).name, "2026-11-11-03-pr-123-pagination.md")
            other = store.report_path(root, {**target, "repository": "github.com/fork/antares"}, day)
            self.assertEqual(other.relative_to(root).as_posix(), "fork-antares/2026-11-11-01-pr-123-pagination.md")
            nxt = store.report_path(root, target, day + dt.timedelta(days=1))
            self.assertEqual(nxt.name, "2026-11-12-01-pr-123-pagination.md")

    def test_frontmatter_roundtrip_and_validation(self):
        meta = {"schema_version": 1, "repository": "github.com/a/b", "finding_ids": ["F1"], "title": 'Quoted "title": value'}
        body = "### F1: Regression\nEvidence.\n"
        actual, result = store.decode(store.encode(meta, body))
        self.assertEqual(actual, meta)
        self.assertEqual(result.strip(), body.strip())
        with self.assertRaisesRegex(store.StoreError, "unique"):
            store.finding_ids("### F1: First\n### F1: Second\n")
        with self.assertRaisesRegex(store.StoreError, "helper-generated"):
            store.decode("---\ntitle: bare yaml\n---\nbody")


class InstallationTests(unittest.TestCase):
    def test_install_skills_installs_one_shared_copy_and_working_links(self):
        if not shutil.which("zsh") or not shutil.which("rsync"):
            self.skipTest("zsh and rsync are required for installer checks")
        with tempfile.TemporaryDirectory(prefix="install-skills-") as tmp:
            home = Path(tmp).resolve()
            env = dict(os.environ, GOERWIN_SKILLS_HOME=tmp, HOME=tmp, PYTHONDONTWRITEBYTECODE="1")
            subprocess.run(["zsh", "bin/install-skills.zsh"], cwd=ROOT, env=env, check=True, capture_output=True)
            for name in ("goerwin-wts", "goerwin-review"):
                command = home / ".local/bin" / name
                self.assertTrue(command.is_symlink())
                subprocess.run([str(command), "--help"], check=True, env=env, capture_output=True)
            self.assertFalse(list(home.glob(".agents/**/tests")))
            for skill, args in (("goerwin-code-review", ["review_pr.py", "presets"]),
                               ("goerwin-receiving-code-review", ["receiving.py", "--help"]),
                               ("goerwin-review-loop", ["review_loop.py", "--help"])):
                scripts = home / ".agents/skills" / skill / "scripts"
                self.assertTrue((scripts / "goerwin_tools").is_symlink())
                self.assertEqual((scripts / "goerwin_tools").resolve(), home / ".agents/shared/goerwin_tools")
                subprocess.run([sys.executable, str(scripts / args[0]), *args[1:]], check=True, env=env, capture_output=True)
