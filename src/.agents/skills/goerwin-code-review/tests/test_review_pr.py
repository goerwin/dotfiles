import argparse
import concurrent.futures
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import review_pr as review
import contextlib
from goerwin_tools import harness, herdr_adapter, review_store as store, targets


class WorkflowFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="review-pr-test-")
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "source repo $(not-a-command)"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Review Tests")
        self.git("config", "user.email", "review-tests@example.invalid")
        (self.repo / "code.txt").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("remote", "add", "origin", "https://github.com/example/project.git")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.developer = self.root / "developer tree"
        self.git("worktree", "add", "-b", "feature", str(self.developer), "main")
        (self.developer / "code.txt").write_text("changed\n")
        self.git("add", "code.txt", cwd=self.developer)
        self.git("commit", "-m", "feature", cwd=self.developer)
        self.head = self.git("rev-parse", "HEAD", cwd=self.developer)
        (self.developer / "uncommitted.txt").write_text("personal work\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "harness-log.json"
        self.archive = self.root / "archive"
        self.harness = self.executable(
            "codex",
            """
            import json, os, sys
            from pathlib import Path
            Path(os.environ["REVIEW_TEST_LOG"]).write_text(json.dumps({
                "argv":sys.argv[1:],
                "cwd":os.getcwd(),
                "effort_env":os.environ.get("CLAUDE_CODE_EFFORT_LEVEL"),
                "nested_env":os.environ.get("CLAUDECODE"),
            }))
            if os.environ.get("REVIEW_TEST_REPORT"):
                Path(os.environ["REVIEW_TEST_REPORT"]).write_text("# Review\\nNo findings.\\n")
            """,
        )
        self.executable(
            "wt",
            """
            import json, os, subprocess, sys
            from pathlib import Path
            args=sys.argv[1:]
            repo=args[args.index("-C")+1]
            create="--create" in args
            branch=args[args.index("--create")+1] if create else args[args.index("switch")+1]
            base=args[args.index("--base")+1] if "--base" in args else None
            folder=Path(os.environ["REVIEW_TEST_WT_ROOT"])/branch.replace("/","__")
            command=["git","-C",repo,"worktree","add"]
            command += ["-b",branch,str(folder),base] if create else [str(folder),branch]
            subprocess.run(command,check=True,stdout=sys.stderr)
            hook=os.environ.get("REVIEW_TEST_HOOK")
            hook and (folder/hook).write_text("written by a setup hook")
            print(json.dumps({"path":str(folder)}))
            """,
        )
        self.environment = patch.dict(
            os.environ,
            {
                "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                "REVIEW_TEST_WT_ROOT": str(self.root / "review worktrees"),
                "REVIEW_TEST_LOG": str(self.log),
                "GOERWIN_CODE_REVIEWS_DIR": str(self.archive),
            },
        )
        (self.bin / "claude").symlink_to(self.harness)
        self.environment.start()
        self.opened = []
        self.snapshot_patch = patch.object(herdr_adapter, "snapshot", return_value={"spaces": []})
        self.open_patch = patch.object(herdr_adapter, "open_review", side_effect=self.open_review)
        self.snapshot_patch.start()
        self.open_patch.start()
        self.target_file = self.root / "target.json"
        self.target = review.comparison_target(self.developer, "feature", "main")
        review.json_write(self.target_file, {"status": "ready", "target": self.target})

    def tearDown(self):
        self.open_patch.stop()
        self.snapshot_patch.stop()
        self.environment.stop()
        self.temporary.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def executable(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body).lstrip())
        path.chmod(0o755)
        return path

    def open_review(self, *args):
        self.opened.append(args)
        return {"space": "space-test", "tab": f"tab-{len(self.opened)}", "terminal": "terminal-test", "warnings": []}

    def launch(self, preset="sol-high", dry_run=False):
        return review.launch(argparse.Namespace(
            target_file=str(self.target_file), preset=preset,
            presets=str(harness.PRESETS), archive=None, dry_run=dry_run,
            headless=False, context_file=None,
        ))

    def resolve_args(self, **kwargs):
        values = dict(
            cwd=str(self.developer),
            github_user=None, input=None, head=None, base=None, instructions="", rubric="default", in_place=False,
            revision="pr",
        )
        values.update(kwargs)
        return argparse.Namespace(**values)

    def pr(self, **kwargs):
        data = {
            "id": "PR_test", "number": 123, "url": "https://github.com/example/project/pull/123",
            "title": "Feature", "state": "OPEN", "headRefName": "feature",
            "baseRefName": "main", "headRefOid": self.head, "baseRefOid": self.base,
        }
        data.update(kwargs)
        return data

    def github(self, prs):
        def fake(args, cwd, user=None, host=None):
            if args[:2] == ["repo", "view"]:
                return {"nameWithOwner": "example/project", "url": "https://github.com/example/project"}
            if args[:2] == ["pr", "list"]:
                return prs
            if args[:2] == ["pr", "view"]:
                return prs[0]
            raise AssertionError(args)
        return fake

    @contextlib.contextmanager
    def fake_github(self, **behavior):
        with patch.object(review, "github", **behavior), patch.object(targets, "github", **behavior):
            yield

    def complete(self, result):
        Path(result["report"]).write_text("# Review\nNo findings.\n")
        review.finish(argparse.Namespace(run_file=result["run_file"]))

class WorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_local_presets_build_exact_non_shell_arguments(self):
        choices = harness.presets()
        self.assertEqual(len(choices), 5)
        sol = next(item for item in choices if item["id"] == "sol-xhigh")
        self.assertEqual(harness.argv(sol), [
            "codex", "--no-daemon", "--model", "gpt-6.1-sol",
            "-c", 'model_reasoning_effort="xhigh"',
        ])
        opus = next(item for item in choices if item["id"] == "opus-high")
        self.assertEqual(harness.argv(opus), [
            "claude", "--model", "claude-opus-5-5", "--effort", "high",
        ])

    def test_no_input_synced_pr_ignores_source_dirt(self):
        before = self.git("status", "--porcelain", cwd=self.developer)
        with self.fake_github(side_effect=self.github([self.pr()])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["target"]["source_root"], str(self.repo))
        self.assertEqual(result["target"]["head_sha"], self.head)
        self.assertEqual(self.git("status", "--porcelain", cwd=self.developer), before)

    def test_unsynced_pr_requires_revision_selection(self):
        with self.fake_github(side_effect=self.github([self.pr(headRefOid=self.base)])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "revision_selection_required")
        self.assertEqual(result["local_head_sha"], self.head)
        self.assertEqual(result["pr_head_sha"], self.base)
        self.assertFalse(self.archive.exists())

    def test_no_pr_and_multiple_prs_never_launch_implicitly(self):
        with self.fake_github(side_effect=self.github([])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "comparison_confirmation_required")
        self.assertEqual((result["head"], result["base"]), ("feature", "origin/main"))
        with self.fake_github(side_effect=self.github([self.pr(), self.pr(number=124)])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "pr_selection_required")
        self.assertFalse(self.opened)

    def test_failed_github_lookup_is_not_treated_as_no_pr(self):
        with self.fake_github(side_effect=review.ReviewError("authentication failed")):
            with self.assertRaisesRegex(review.ReviewError, "authentication"):
                review.inspect_target(self.resolve_args())

    def test_custom_input_requires_resolution_and_unknown_repo_is_not_cloned(self):
        result = review.inspect_target(self.resolve_args(input="review caching against main"))
        self.assertEqual(result["status"], "clarification_required")
        with self.assertRaisesRegex(review.ReviewError, "never cloned"):
            review.inspect_target(self.resolve_args(input="https://github.com/other/repo/pull/123"))

    def test_explicit_local_revision_uses_invoking_worktree_head(self):
        with self.fake_github(return_value=self.pr(headRefOid=self.base)):
            result = review.inspect_target(self.resolve_args(
                input="https://github.com/example/project/pull/123", revision="local",
            ))
        self.assertEqual(result["target"]["head_sha"], self.head)
        self.assertEqual(result["target"]["pr_head_sha"], self.base)
        self.assertEqual(result["target"]["revision"], "local")

    def test_dry_run_makes_no_worktree_report_or_tab(self):
        before = review.worktrees(self.repo)
        result = self.launch("sol-xhigh", dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertIn('model_reasoning_effort="xhigh"', result["argv"])
        self.assertEqual(review.worktrees(self.repo), before)
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.opened)

    def test_launch_uses_central_archive_and_preserves_developer_tree(self):
        before = self.git("status", "--porcelain", cwd=self.developer)
        result = self.launch()
        record = review.json_read(result["run_file"])
        self.assertEqual(Path(result["report"]).parent, self.archive / "project")
        self.assertRegex(Path(result["report"]).name, r"^\d{4}-\d\d-\d\d-01-feature-against-main\.md$")
        self.assertNotEqual(result["worktree"], str(self.developer))
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=result["worktree"]), self.head)
        self.assertEqual(self.git("branch", "--show-current", cwd=self.developer), "feature")
        self.assertEqual(self.git("status", "--porcelain", cwd=self.developer), before)
        self.assertEqual(record["target"]["merge_base_sha"], self.base)
        self.assertEqual(self.opened[0][2][2], "_run")
        self.assertIn(result["report"], self.opened[0][3])
        self.assertIn("NOT a request to invoke", self.opened[0][3])

    def test_parallel_same_target_same_or_different_model_gets_separate_checkouts(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(self.launch, preset)
                for preset in ("sol-high", "sol-high", "opus-xhigh")
            ]
            results = [future.result() for future in futures]
        self.assertEqual(len({item["worktree"] for item in results}), 3)
        self.assertEqual(len({item["report"] for item in results}), 3)
        self.assertTrue(all(item["status"] == "launched" for item in results))

    def test_completed_clean_exact_checkout_is_reused_in_a_new_tab(self):
        first = self.launch()
        self.complete(first)
        second = self.launch()
        self.assertTrue(second["reused"])
        self.assertEqual(first["worktree"], second["worktree"])
        self.assertNotEqual(first["report"], second["report"])
        self.assertNotEqual(first["tab"], second["tab"])

    def test_dirty_completed_checkout_causes_fresh_allocation_without_overwrite(self):
        first = self.launch()
        self.complete(first)
        dirty = Path(first["worktree"]) / "personal.txt"
        dirty.write_text("leave me alone\n")
        second = self.launch()
        self.assertNotEqual(first["worktree"], second["worktree"])
        self.assertEqual(dirty.read_text(), "leave me alone\n")

    def test_unexpected_commits_are_preserved_and_another_checkout_is_created(self):
        first = self.launch()
        self.complete(first)
        (Path(first["worktree"]) / "code.txt").write_text("manual commit\n")
        self.git("add", ".", cwd=first["worktree"])
        self.git("commit", "-m", "manual", cwd=first["worktree"])
        manual = self.git("rev-parse", "HEAD", cwd=first["worktree"])
        second = self.launch()
        self.assertNotEqual(first["worktree"], second["worktree"])
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=first["worktree"]), manual)

    def test_completed_but_still_live_agent_prevents_reuse_not_new_review(self):
        first = self.launch()
        self.complete(first)
        review.update_record(first["run_file"], {"pid": os.getpid()})
        second = self.launch()
        self.assertNotEqual(first["worktree"], second["worktree"])

    def test_dead_running_or_failed_launch_does_not_block_reuse(self):
        first = self.launch()
        review.update_record(first["run_file"], {"status": "running", "pid": 2**22 + 1})
        self.assertTrue(self.launch()["reused"])
        stuck = review.json_read(first["run_file"])
        self.assertFalse(review.is_busy({**stuck, "status": "launch_failed", "pid": None}))
        self.assertTrue(review.is_busy({**stuck, "status": "launching", "pid": None, "reserved_at": review.time.time()}))

    def test_adversarial_rubric_reaches_prompt_frontmatter_and_filename(self):
        resolved = review.inspect_target(self.resolve_args(head="feature", base="main", rubric="adversarial"))
        review.json_write(self.target_file, resolved)
        result = self.launch()
        prompt = self.opened[0][3]
        self.assertIn("# Rubric: adversarial", prompt)
        self.assertNotIn("# Rubric: default", prompt)
        self.assertTrue(Path(result["report"]).name.endswith("-feature-against-main-adversarial.md"))
        self.complete(result)
        self.assertEqual(store.read_report(result["report"])["metadata"]["rubric"], "adversarial")
        review.json_write(self.target_file, {"status": "ready", "target": {**self.target, "rubric": "lenient"}})
        with self.assertRaisesRegex(review.ReviewError, "Unknown rubric"):
            self.launch()
        self.assertEqual(len(self.opened), 1)

    def test_in_place_reviews_this_checkout_with_warnings_instead_of_questions(self):
        with self.fake_github(side_effect=self.github([self.pr()])):
            synced = review.inspect_target(self.resolve_args(in_place=True))
        self.assertEqual(synced["status"], "ready")
        self.assertEqual(synced["warnings"], ["The worktree has uncommitted changes; they are included in the review."])
        self.assertTrue(synced["target"]["includes_uncommitted"])
        self.assertEqual(synced["target"]["invoking_checkout"], str(self.developer))
        (self.developer / "uncommitted.txt").unlink()
        with self.fake_github(side_effect=self.github([self.pr(headRefOid=self.base)])):
            unsynced = review.inspect_target(self.resolve_args(in_place=True))
        self.assertEqual(unsynced["status"], "ready")
        self.assertIn("differs from the PR head", unsynced["warnings"][0])
        self.assertEqual((unsynced["target"]["head_sha"], unsynced["target"]["base_ref"]), (self.head, "main"))
        self.assertFalse(unsynced["target"]["includes_uncommitted"])
        with self.fake_github(side_effect=self.github([])):
            no_pr = review.inspect_target(self.resolve_args(in_place=True))
        self.assertEqual((no_pr["status"], no_pr["target"]["base_ref"], no_pr["warnings"]), ("ready", "origin/main", []))

    def test_setup_hooks_may_add_files_but_not_change_tracked_source(self):
        with patch.dict(os.environ, {"REVIEW_TEST_HOOK": "node_modules.marker"}):
            self.assertEqual(self.launch()["status"], "launched")
        with patch.dict(os.environ, {"REVIEW_TEST_HOOK": "code.txt"}):
            with self.assertRaisesRegex(review.ReviewError, "changed tracked files"):
                self.launch()

    def test_head_comparison_records_its_development_branch(self):
        target = review.comparison_target(self.developer, "HEAD", "main")
        self.assertEqual(target["development_branch"], "feature")

    def test_changed_pr_or_comparison_requires_new_resolution_before_side_effects(self):
        with self.fake_github(return_value=self.pr()):
            target = review.pr_target(self.developer, self.pr()["url"])
        review.json_write(self.target_file, {"status": "ready", "target": target})
        with self.fake_github(return_value=self.pr(headRefOid=self.base)):
            result = self.launch()
        self.assertEqual(result["status"], "revision_selection_required")
        self.assertFalse(self.archive.exists())
        review.json_write(self.target_file, {"status": "ready", "target": self.target})
        self.git("update-ref", "refs/heads/main", self.head)
        result = self.launch()
        self.assertEqual(result["status"], "revision_selection_required")
        self.assertFalse(self.opened)

    def test_supervisor_honors_exact_model_effort_and_completes_report(self):
        result = self.launch("opus-xhigh")
        task = 'Review this literal text: $(touch SHOULD_NOT_EXIST); "quoted"'
        env = {
            **os.environ, "REVIEW_TEST_REPORT": result["report"],
            "CLAUDE_CODE_EFFORT_LEVEL": "low", "CLAUDECODE": "parent-session",
        }
        process = subprocess.run(
            [
                sys.executable, str(SKILL / "scripts/review_pr.py"), "_run",
                "--run-file", result["run_file"], task,
            ],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        logged = review.json_read(self.log)
        self.assertEqual(logged["argv"], ["--model", "claude-opus-5-5", "--effort", "xhigh", task])
        self.assertIsNone(logged["effort_env"])
        self.assertIsNone(logged["nested_env"])
        self.assertEqual(logged["cwd"], result["worktree"])
        self.assertEqual(review.json_read(result["run_file"])["status"], "completed")
        self.assertFalse((Path(result["worktree"]) / "SHOULD_NOT_EXIST").exists())

    def test_finish_requires_a_report_and_missing_report_is_a_failed_run(self):
        result = self.launch()
        with self.assertRaisesRegex(review.ReviewError, "nonempty report"):
            review.finish(argparse.Namespace(run_file=result["run_file"]))
        process = subprocess.run(
            [
                sys.executable, str(SKILL / "scripts/review_pr.py"), "_run",
                "--run-file", result["run_file"], "Review without a report",
            ],
            env=os.environ.copy(), capture_output=True, text=True,
        )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(review.json_read(result["run_file"])["status"], "failed")

    def test_unresolved_target_cannot_be_launched(self):
        review.json_write(self.target_file, {"status": "revision_selection_required"})
        with self.assertRaisesRegex(review.ReviewError, "clarification"):
            self.launch()
        self.assertFalse(self.opened)

    def test_generated_metadata_is_complete_and_finalization_is_immutable(self):
        result = self.launch("sol-xhigh")
        self.complete(result)
        saved = store.read_report(result["report"])
        meta = saved["metadata"]
        self.assertEqual(meta["review_id"], result["run_id"])
        self.assertEqual(meta["repository"], "github.com/example/project")
        self.assertEqual(meta["source_path"], str(self.repo))
        self.assertEqual(meta["head_sha"], self.head)
        self.assertEqual(meta["base_sha"], self.base)
        self.assertEqual(meta["model"], "gpt-6.1-sol")
        self.assertEqual(meta["effort"], "xhigh")
        self.assertEqual(meta["finding_ids"], [])
        before = Path(result["report"]).read_bytes()
        review.finish(argparse.Namespace(run_file=result["run_file"]))
        self.assertEqual(Path(result["report"]).read_bytes(), before)
        Path(result["report"]).write_text("changed by an external editor\n")
        with self.assertRaisesRegex(store.StoreError, "changed"):
            review.finish(argparse.Namespace(run_file=result["run_file"]))


if __name__ == "__main__":
    unittest.main()
