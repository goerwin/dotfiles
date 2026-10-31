import argparse
import concurrent.futures
import datetime as dt
import importlib.util
import json
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
from goerwin_tools import herdr_adapter, review_store as store, worktrees

receiver_spec = importlib.util.spec_from_file_location(
    "receiving", SKILL.parent / "goerwin-receiving-code-review/scripts/receiving.py"
)
receiving = importlib.util.module_from_spec(receiver_spec)
receiver_spec.loader.exec_module(receiving)


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
            "fake-harness",
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
        self.environment.start()
        preset_data = review.presets(SKILL / "presets.json")
        for item in preset_data:
            item["command"] = str(self.harness)
        self.preset_file = self.root / "presets.json"
        review.json_write(self.preset_file, preset_data)
        self.opened = []
        self.snapshot_patch = patch.object(herdr_adapter, "snapshot", return_value={"spaces": []})
        self.open_patch = patch.object(herdr_adapter, "open_review", side_effect=self.open_review)
        self.snapshot_patch.start()
        self.open_patch.start()
        self.focus_patch = patch.object(herdr_adapter, "focus_worktree", return_value={"available": False})
        self.focus_patch.start()
        self.target_file = self.root / "target.json"
        self.target = review.comparison_target(self.developer, "feature", "main")
        review.json_write(self.target_file, {"status": "ready", "target": self.target})

    def tearDown(self):
        self.focus_patch.stop()
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
            presets=str(self.preset_file), adapter="herdr", dry_run=dry_run,
        ))

    def resolve_args(self, **kwargs):
        values = dict(
            cwd=str(self.developer), config=str(self.root / "config.json"),
            github_user=None, input=None, head=None, base=None, instructions="",
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

    def complete(self, result):
        Path(result["report"]).write_text("# Review\nNo findings.\n")
        review.finish(argparse.Namespace(run_file=result["run_file"]))

class WorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_local_presets_build_exact_non_shell_arguments(self):
        choices = review.presets(SKILL / "presets.json")
        self.assertEqual(len(choices), 5)
        sol = next(item for item in choices if item["id"] == "sol-xhigh")
        self.assertEqual(review.harness_argv(sol), [
            "codex", "--no-daemon", "--model", "gpt-6.1-sol",
            "-c", 'model_reasoning_effort="xhigh"',
        ])
        opus = next(item for item in choices if item["id"] == "opus-high")
        self.assertEqual(review.harness_argv(opus), [
            "claude", "--model", "claude-opus-5-5", "--effort", "high",
        ])

    def test_no_input_synced_pr_ignores_source_dirt(self):
        before = self.git("status", "--porcelain", cwd=self.developer)
        with patch.object(review, "github", side_effect=self.github([self.pr()])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["target"]["source_root"], str(self.repo))
        self.assertEqual(result["target"]["head_sha"], self.head)
        self.assertEqual(self.git("status", "--porcelain", cwd=self.developer), before)

    def test_unsynced_pr_requires_revision_selection(self):
        with patch.object(review, "github", side_effect=self.github([self.pr(headRefOid=self.base)])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "revision_selection_required")
        self.assertEqual(result["local_head_sha"], self.head)
        self.assertEqual(result["pr_head_sha"], self.base)
        self.assertFalse(self.archive.exists())

    def test_no_pr_and_multiple_prs_never_launch_implicitly(self):
        with patch.object(review, "github", side_effect=self.github([])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "comparison_confirmation_required")
        self.assertEqual((result["head"], result["base"]), ("feature", "main"))
        with patch.object(review, "github", side_effect=self.github([self.pr(), self.pr(number=124)])):
            result = review.inspect_target(self.resolve_args())
        self.assertEqual(result["status"], "pr_selection_required")
        self.assertFalse(self.opened)

    def test_failed_github_lookup_is_not_treated_as_no_pr(self):
        with patch.object(review, "github", side_effect=review.ReviewError("authentication failed")):
            with self.assertRaisesRegex(review.ReviewError, "authentication"):
                review.inspect_target(self.resolve_args())

    def test_custom_input_requires_resolution_and_unknown_repo_is_not_cloned(self):
        result = review.inspect_target(self.resolve_args(input="review caching against main"))
        self.assertEqual(result["status"], "clarification_required")
        with self.assertRaisesRegex(review.ReviewError, "registered"):
            review.inspect_target(self.resolve_args(input="https://github.com/other/repo/pull/123"))

    def test_explicit_local_revision_uses_invoking_worktree_head(self):
        with patch.object(review, "github", return_value=self.pr(headRefOid=self.base)):
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
        self.assertEqual(Path(result["report"]).parent, self.archive)
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

    def test_changed_pr_or_comparison_requires_new_resolution_before_side_effects(self):
        with patch.object(review, "github", return_value=self.pr()):
            target = review.pr_target(self.developer, self.pr()["url"], {})
        review.json_write(self.target_file, {"status": "ready", "target": target})
        with patch.object(review, "github", return_value=self.pr(headRefOid=self.base)):
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

    def test_list_filters_project_branch_and_preserves_global_browsing(self):
        first = self.launch("sol-high")
        self.complete(first)
        args = argparse.Namespace(cwd=str(self.developer), archive=None, all=False, all_branches=False, pr=None)
        self.assertEqual(len(review.list_reviews(args)["reviews"]), 1)
        args.cwd = str(self.repo)
        self.assertEqual(review.list_reviews(args)["reviews"], [])
        args.all_branches = True
        self.assertEqual(len(review.list_reviews(args)["reviews"]), 1)
        args.all = True
        args.cwd = str(self.root)
        self.assertEqual(len(review.list_reviews(args)["reviews"]), 1)


class ArchiveTests(unittest.TestCase):
    def test_filename_uses_local_time_readable_fields_and_collision_counter(self):
        with tempfile.TemporaryDirectory() as directory:
            moment = dt.datetime(2026, 10, 30, 22, 30, 15, tzinfo=dt.timezone(dt.timedelta(hours=-5)))
            target = {"source_root": "/projects/antares", "kind": "pr", "pr_number": 123, "title": "Pagination"}
            preset = {"model": "gpt-6.1-sol", "effort": "xhigh", "filename_model": "sol-6.1"}
            first = store.report_path(directory, target, preset, moment)
            first.write_text("keep this review")
            second = store.report_path(directory, target, preset, moment)
            self.assertEqual(first.name, "2026-10-30_antares_pr-123-pagination_sol-6.1-xhigh_223015.md")
            self.assertEqual(second.stem, first.stem + "_2")
            self.assertNotIn("__", first.name)
            self.assertEqual(first.read_text(), "keep this review")

    def test_frontmatter_roundtrip_and_duplicate_finding_rejection(self):
        meta = {"schema_version": 1, "repository": "github.com/a/b", "finding_ids": ["F1"], "title": 'Quoted "title": value'}
        body = "### F1: Regression\nEvidence.\n"
        actual, result = store.decode(store.encode(meta, body))
        self.assertEqual(actual, meta)
        self.assertEqual(result.strip(), body.strip())
        with self.assertRaisesRegex(store.StoreError, "unique"):
            store.finding_ids("### F1: First\n### F1: Second\n")


class ReceivingTests(WorkflowFixture, unittest.TestCase):
    def make_report(self, preset="sol-high", finding_id="F1"):
        result = self.launch(preset)
        Path(result["report"]).write_text(
            f"# Review\n\n### {finding_id}: Pagination cursor is lost\n"
            "Location: code.txt:1\nClassification: blocking\nEvidence: The caller passes a cursor.\n"
        )
        review.finish(argparse.Namespace(run_file=result["run_file"]))
        return result

    def prepare(self, paths=(), **overrides):
        values = dict(
            cwd=str(self.developer), archive=None, review=list(paths), text_file=None,
            confirm_unversioned=False, confirm_branch=False, github_user=None,
        )
        values.update(overrides)
        return receiving.prepare(argparse.Namespace(**values))

    def record(self, session, outcomes):
        path = self.root / "outcomes.json"
        review.json_write(path, outcomes)
        return receiving.record(argparse.Namespace(session_file=session["session_file"], outcomes=str(path)))

    def outcome(self, sources, outcome="applied"):
        return {
            "sources": sources, "outcome": outcome,
            "explanation": "Preserved the cursor in the caller.",
            "evidence": "The current caller passes a cursor; the focused regression verifies it.",
        }

    def test_duplicate_findings_share_one_outcome_without_changing_originals(self):
        first, second = self.make_report(), self.make_report("opus-high", "F2")
        before = {item["report"]: Path(item["report"]).read_bytes() for item in (first, second)}
        session = self.prepare([first["report"], second["report"]])
        self.assertEqual(session["status"], "ready")
        sources = [item["source"] for item in session["findings"]]
        (self.developer / "code.txt").write_text("fixed cursor\n")
        result = self.record(session, [self.outcome(sources)])
        metadata, body = store.decode(Path(result["receipt"]).read_text())
        self.assertEqual(len(metadata["outcomes"]), 1)
        self.assertEqual(metadata["outcomes"][0]["sources"], sources)
        self.assertTrue(all(source in body for source in sources))
        for path, content in before.items():
            self.assertEqual(Path(path).read_bytes(), content)
        listed = review.list_reviews(argparse.Namespace(
            cwd=str(self.developer), archive=None, all=False, all_branches=False, pr=None,
        ))["reviews"]
        self.assertTrue(all(item["receiving"]["remaining"] == 0 for item in listed))

    def test_addressed_findings_skip_and_waiting_findings_remain_active(self):
        report = self.make_report()
        session = self.prepare([report["report"]])
        source = session["findings"][0]["source"]
        waiting = self.outcome([source], "waiting")
        with self.assertRaisesRegex(review.ReviewError, "question"):
            self.record(session, [waiting])
        waiting["question"] = "Should the cursor persist after filters change?"
        self.record(session, [waiting])
        next_session = self.prepare([report["report"]])
        self.assertTrue(next_session["findings"][0]["active"])
        self.record(next_session, [self.outcome([source], "pushed_back")])
        final = self.prepare([report["report"]])
        self.assertFalse(final["findings"][0]["active"])
        self.record(final, [])

    def test_stale_review_is_revalidated_instead_of_automatically_rejected(self):
        report = self.make_report()
        (self.developer / "code.txt").write_text("later committed fix\n")
        self.git("add", "code.txt", cwd=self.developer)
        self.git("commit", "-m", "later fix", cwd=self.developer)
        session = self.prepare([report["report"]])
        self.assertEqual(session["status"], "ready")
        self.assertTrue(session["inputs"][0]["stale"])
        self.assertTrue(session["findings"][0]["active"])

    def test_branch_mismatch_requires_confirmation_without_switching(self):
        report = self.make_report()
        result = self.prepare([report["report"]], cwd=str(self.repo))
        self.assertEqual(result["status"], "branch_confirmation_required")
        self.assertEqual(self.git("branch", "--show-current"), "main")
        confirmed = self.prepare([report["report"]], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(confirmed["status"], "ready")
        self.assertEqual(confirmed["cwd"], str(self.developer))
        self.assertEqual(confirmed["branch"], "feature")
        self.assertEqual(self.git("branch", "--show-current"), "main")

    def test_receiving_recreates_a_missing_development_worktree(self):
        report = self.make_report()
        self.git("worktree", "remove", "--force", str(self.developer))
        session = self.prepare([report["report"]], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(session["status"], "ready")
        self.assertEqual(session["branch"], "feature")
        self.assertEqual(session["head_before"], self.head)
        self.assertNotEqual(session["cwd"], str(self.repo))
        self.assertEqual(self.git("branch", "--show-current"), "main")

    def test_head_comparison_retains_its_development_branch_for_receiving(self):
        self.target = review.comparison_target(self.developer, "HEAD", "main")
        review.json_write(self.target_file, {"status": "ready", "target": self.target})
        report = self.make_report()
        session = self.prepare([report["report"]], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(session["cwd"], str(self.developer))
        self.assertEqual(session["branch"], "feature")

    def test_local_pr_receiving_restores_the_recorded_development_branch(self):
        pr = self.pr(headRefName="remote-feature")
        with patch.object(review, "github", side_effect=self.github([pr])):
            self.target = review.pr_target(self.developer, pr["url"], {}, revision="local")
            review.json_write(self.target_file, {"status": "ready", "target": self.target})
            report = self.make_report()
        self.git("worktree", "remove", "--force", str(self.developer))
        with patch.object(worktrees, "switch", side_effect=AssertionError("Use the recorded local branch")):
            session = self.prepare([report["report"]], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(session["branch"], "feature")
        self.assertEqual(session["head_before"], self.head)

    def test_legacy_unnamed_report_requires_development_branch_selection(self):
        report = self.make_report()
        metadata, body = store.decode(Path(report["report"]).read_text())
        metadata.pop("development_branch", None)
        metadata["head_ref"] = "HEAD"
        legacy = self.root / "legacy.md"
        legacy.write_text(store.encode(metadata, body))
        result = self.prepare([str(legacy)], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(result["status"], "branch_selection_required")
        selected = self.prepare([str(legacy)], cwd=str(self.repo), confirm_branch=True, branch="feature")
        self.assertEqual(selected["cwd"], str(self.developer))

    def test_plain_paste_requires_context_and_preserves_its_input(self):
        pasted = self.root / "pasted.txt"
        pasted.write_text("1. code.txt:1 Check the cursor.\n2. code.txt:2 Validate the next page.\n")
        before = pasted.read_bytes()
        result = self.prepare(text_file=str(pasted))
        self.assertEqual(result["status"], "context_confirmation_required")
        self.assertFalse((self.archive / ".inputs").exists())
        session = self.prepare(text_file=str(pasted), confirm_unversioned=True)
        self.assertEqual(len(session["findings"]), 2)
        self.assertTrue(session["inputs"][0]["unversioned"])
        self.assertEqual(pasted.read_bytes(), before)
        self.assertTrue(Path(session["inputs"][0]["path"]).is_file())

    def test_pasted_full_report_retains_its_provenance_and_progress(self):
        report = self.make_report()
        pasted = self.root / "full-pasted.md"
        pasted.write_text(Path(report["report"]).read_text())
        session = self.prepare(text_file=str(pasted))
        self.assertEqual(session["inputs"][0]["review_id"], report["run_id"])
        source = session["findings"][0]["source"]
        self.record(session, [self.outcome([source])])
        again = self.prepare([report["report"]])
        self.assertFalse(again["findings"][0]["active"])

    def test_coverage_and_immutable_inputs_are_enforced(self):
        report = self.make_report()
        session = self.prepare([report["report"]])
        with self.assertRaisesRegex(review.ReviewError, "every active"):
            self.record(session, [])
        Path(report["report"]).write_text("external modification\n")
        with self.assertRaisesRegex(review.ReviewError, "changed"):
            self.record(session, [self.outcome([session["findings"][0]["source"]])])

    def test_duplicate_recording_and_head_changes_are_rejected(self):
        report = self.make_report()
        session = self.prepare([report["report"]])
        outcomes = [self.outcome([session["findings"][0]["source"]])]
        self.record(session, outcomes)
        with self.assertRaisesRegex(review.ReviewError, "already recorded"):
            self.record(session, outcomes)
        pending = self.prepare([report["report"]])
        (self.developer / "code.txt").write_text("another commit\n")
        self.git("add", "code.txt", cwd=self.developer)
        self.git("commit", "-m", "changed head", cwd=self.developer)
        with self.assertRaisesRegex(review.ReviewError, "HEAD changed"):
            self.record(pending, [])


class HerdrAdapterTests(unittest.TestCase):
    def test_exact_folder_matching_and_focus_warning_do_not_duplicate_launch(self):
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


if __name__ == "__main__":
    unittest.main()
