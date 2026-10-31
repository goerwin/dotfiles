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
import receiving
from goerwin_tools import herdr_adapter, review_store as store, runtime, worktrees


class ReceivingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="receiving-test-")
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "source repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Receiving Tests")
        self.git("config", "user.email", "tests@example.invalid")
        (self.repo / "code.txt").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("remote", "add", "origin", "https://github.com/example/project.git")
        self.developer = self.root / "developer tree"
        self.git("worktree", "add", "-b", "feature", str(self.developer), "main")
        self.commit("changed\n")
        self.head = self.git("rev-parse", "HEAD", cwd=self.developer)
        self.archive = self.root / "archive"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        wt = bin_dir / "wt"
        wt.write_text(f"#!{sys.executable}\n" + textwrap.dedent('''
            import json, os, subprocess, sys
            from pathlib import Path
            args = sys.argv[1:]
            repo, branch = args[args.index("-C") + 1], args[args.index("switch") + 1]
            folder = Path(os.environ["RECEIVING_TEST_WT_ROOT"]) / branch.replace("/", "__")
            subprocess.run(["git", "-C", repo, "worktree", "add", str(folder), branch], check=True, stdout=sys.stderr)
            print(json.dumps({"path": str(folder)}))
        ''').lstrip())
        wt.chmod(0o755)
        self.environment = patch.dict(os.environ, {
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "RECEIVING_TEST_WT_ROOT": str(self.root / "worktrees"),
            "GOERWIN_CODE_REVIEWS_DIR": str(self.archive),
        })
        self.environment.start()
        self.focus = patch.object(herdr_adapter, "focus_worktree", return_value={"available": False})
        self.focus.start()
        self.reports = 0

    def tearDown(self):
        self.focus.stop()
        self.environment.stop()
        self.temporary.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or self.repo), *args],
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, text):
        (self.developer / "code.txt").write_text(text)
        self.git("commit", "-am", "change", cwd=self.developer)

    def make_report(self, finding_id="F1", **target):
        self.reports += 1
        target = {
            "kind": "comparison", "source_root": str(self.repo), "common_dir": runtime.common_dir(self.repo),
            "repository": "github.com/example/project", "target_key": "feature...main", "title": "feature",
            "head_ref": "feature", "development_branch": "feature", "base_ref": "main",
            "head_sha": self.head, "base_sha": self.base, **target,
        }
        preset = {"id": "sol-high", "harness": "codex", "model": "gpt-6.1-sol", "effort": "high"}
        path = self.archive / f"report-{self.reports}.md"
        self.archive.mkdir(exist_ok=True)
        path.write_text(f"# Review\n\n### {finding_id}: Pagination cursor is lost\nEvidence: The caller passes a cursor.\n")
        store.finalize_report({
            "report": str(path), "run_id": f"run-{self.reports}", "created_at": runtime.now(),
            "target": target, "preset": preset,
        })
        return str(path)

    def prepare(self, paths=(), **overrides):
        values = dict(cwd=str(self.developer), review=list(paths), text_file=None,
                      confirm_branch=False, branch=None, github_user=None)
        values.update(overrides)
        return receiving.prepare(type("Args", (), values))

    def record(self, paths, outcomes, cwd=None):
        file = self.root / "outcomes.json"
        file.write_text(json.dumps(outcomes))
        return receiving.record(type("Args", (), dict(
            cwd=str(cwd or self.developer), review=list(paths), outcomes=str(file),
        )))

    def outcome(self, sources, outcome="applied", **extra):
        return {"sources": sources, "outcome": outcome, "explanation": "Preserved the cursor.",
                "evidence": "The caller passes a cursor; the regression verifies it.", **extra}

    def test_grouped_outcome_writes_each_sidecar_and_leaves_originals_untouched(self):
        first, second = self.make_report(), self.make_report("F2")
        before = {path: Path(path).read_bytes() for path in (first, second)}
        session = self.prepare([first, second])
        sources = [item["source"] for item in session["findings"]]
        result = self.record([first, second], [self.outcome(sources)])
        self.assertEqual(len(result["sidecars"]), 2)
        for path, content in before.items():
            self.assertEqual(Path(path).read_bytes(), content)
            text = receiving.sidecar(path).read_text()
            self.assertIn("Grouped with:", text)
        listed = receiving.list_reviews(str(self.developer))["reviews"]
        self.assertEqual([item["remaining"] for item in listed], [0, 0])

    def test_addressed_findings_skip_and_waiting_findings_remain_active(self):
        report = self.make_report()
        source = self.prepare([report])["findings"][0]["source"]
        with self.assertRaisesRegex(runtime.CommandError, "question"):
            self.record([report], [self.outcome([source], "waiting")])
        self.record([report], [self.outcome([source], "waiting", question="Keep the cursor after filtering?")])
        self.assertTrue(self.prepare([report])["findings"][0]["active"])
        self.record([report], [self.outcome([source], "pushed_back")])
        self.assertFalse(self.prepare([report])["findings"][0]["active"])
        self.record([report], [])
        self.assertEqual(receiving.sidecar(report).read_text().count("\n## "), 2)

    def test_coverage_is_enforced(self):
        report = self.make_report()
        with self.assertRaisesRegex(runtime.CommandError, "every active"):
            self.record([report], [])
        with self.assertRaisesRegex(runtime.CommandError, "active, selected"):
            self.record([report], [self.outcome(["run-1:F9"])])

    def test_stale_review_is_revalidated_instead_of_rejected(self):
        report = self.make_report()
        self.commit("later fix\n")
        session = self.prepare([report])
        self.assertTrue(session["reviews"][0]["stale"])
        self.assertTrue(session["findings"][0]["active"])

    def test_branch_mismatch_requires_confirmation_without_switching(self):
        report = self.make_report()
        result = self.prepare([report], cwd=str(self.repo))
        self.assertEqual(result["status"], "branch_confirmation_required")
        confirmed = self.prepare([report], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual((confirmed["cwd"], confirmed["branch"]), (str(self.developer), "feature"))
        self.assertEqual(self.git("branch", "--show-current"), "main")

    def test_missing_development_worktree_is_recreated(self):
        report = self.make_report()
        self.git("worktree", "remove", "--force", str(self.developer))
        session = self.prepare([report], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual((session["branch"], session["head_sha"]), ("feature", self.head))
        self.assertNotEqual(session["cwd"], str(self.repo))

    def test_local_pr_report_uses_its_recorded_development_branch(self):
        report = self.make_report(kind="pr", head_ref="remote-feature", pr_url="https://github.com/example/project/pull/1")
        self.git("worktree", "remove", "--force", str(self.developer))
        with patch.object(worktrees, "switch", side_effect=AssertionError("Use the recorded local branch")):
            session = self.prepare([report], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(session["branch"], "feature")

    def test_unnamed_ref_requires_development_branch_selection(self):
        report = self.make_report(head_ref="HEAD", development_branch=None)
        result = self.prepare([report], cwd=str(self.repo), confirm_branch=True)
        self.assertEqual(result["status"], "branch_selection_required")
        selected = self.prepare([report], cwd=str(self.repo), confirm_branch=True, branch="feature")
        self.assertEqual(selected["cwd"], str(self.developer))

    def test_other_repository_and_mixed_targets_require_selection(self):
        other = self.make_report(repository="github.com/other/repo", common_dir="/elsewhere")
        self.assertEqual(self.prepare([other])["status"], "repository_selection_required")
        mixed = self.prepare([self.make_report(), self.make_report(target_key="other")])
        self.assertEqual(mixed["status"], "target_selection_required")

    def test_pasted_feedback_is_split_but_not_recordable(self):
        pasted = self.root / "pasted.txt"
        pasted.write_text("1. code.txt:1 Check the cursor.\n2. code.txt:2 Validate the next page.\n")
        session = self.prepare(text_file=str(pasted))
        self.assertFalse(session["recordable"])
        self.assertEqual([item["source"] for item in session["findings"]], ["F1", "F2"])
        self.assertFalse(self.archive.exists())

    def test_list_filters_project_and_branch(self):
        self.make_report()
        self.assertEqual(len(receiving.list_reviews(str(self.developer))["reviews"]), 1)
        self.assertEqual(receiving.list_reviews(str(self.repo))["reviews"], [])
        self.assertEqual(len(receiving.list_reviews(str(self.repo), all_branches=True)["reviews"]), 1)
        self.assertEqual(len(receiving.list_reviews(str(self.root), all_projects=True)["reviews"]), 1)


if __name__ == "__main__":
    unittest.main()
