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
import review_loop as loop

AGENT = r'''
import json, os, re, subprocess, sys
from pathlib import Path
prompt = sys.argv[-1]
scenario = json.loads(Path(os.environ["LOOP_SCENARIO"]).read_text())
log = Path(os.environ["LOOP_LOG"])
calls = json.loads(log.read_text()) if log.exists() else []
role = "reviewer" if "Write the Markdown report to:" in prompt else "implementer"
calls.append({"role": role, "argv": sys.argv[1:-1], "prompt": prompt})
log.write_text(json.dumps(calls))
rounds = [call for call in calls if call["role"] == role]
if role == "reviewer":
    findings = scenario["reviews"][min(len(rounds), len(scenario["reviews"])) - 1]
    report = re.search(r"Write the Markdown report to: (.+)", prompt)[1]
    body = "\n".join(f"### F{i}: {title}\n`code.txt:1` · blocking\nEvidence.\n" for i, title in enumerate(findings, 1))
    Path(report).write_text("# Review\n\n" + (body or "No actionable findings.\n"))
    finish = re.search(r"completion command, then summarize.*?\n(.+)$", prompt, re.S)[1]
    subprocess.run(finish, shell=True, check=True, capture_output=True)
else:
    decisions = scenario["decisions"][len(rounds) - 1]
    active = re.findall(r"^\[([^\]]+)\]$", prompt, re.M)
    outcomes = []
    for source, decision in zip(active, decisions):
        item = {"sources": [source], "outcome": decision, "explanation": f"{decision} {source}", "evidence": "checked"}
        if decision == "waiting":
            item["question"] = "Keep the cursor?"
        if decision == "applied":
            with open("code.txt", "a") as stream:
                stream.write(source + "\n")
        outcomes.append(item)
    path = re.search(r"write the outcomes JSON array to (\S+)", prompt)[1]
    Path(path).write_text(json.dumps(outcomes))
    push = subprocess.run(["git", "push", "origin", "HEAD"], capture_output=True)
    Path(os.environ["LOOP_PUSH"]).write_text(str(push.returncode))
    record = re.search(r"\n(\S+ \S+receiving\.py record .+)\n", prompt)[1]
    subprocess.run(record, shell=True, check=True, capture_output=True)
'''


class ReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="review-loop-")
        self.root = Path(self.temporary.name).resolve()
        remote = self.root / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        self.repo = self.root / "project"
        subprocess.run(["git", "clone", "-q", str(remote), str(self.repo)], check=True, capture_output=True)
        self.git("config", "user.name", "Loop Tests")
        self.git("config", "user.email", "tests@example.invalid")
        (self.repo / "code.txt").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("push", "-q", "origin", "main")
        self.git("remote", "set-head", "origin", "main")
        self.git("switch", "-qc", "feature")
        (self.repo / "code.txt").write_text("feature\n")
        self.git("commit", "-qam", "feat: pagination")
        self.git("remote", "add", "github", "https://github.com/example/project.git")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        for name in ("claude", "codex"):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n" + AGENT)
            path.chmod(0o755)
        wt = bin_dir / "wt"
        wt.write_text(f"#!{sys.executable}\n" + textwrap.dedent('''
            import json, os, subprocess, sys
            from pathlib import Path
            args = sys.argv[1:]
            repo, branch = args[args.index("-C") + 1], args[args.index("--create") + 1]
            base = args[args.index("--base") + 1]
            folder = Path(os.environ["LOOP_WT_ROOT"]) / branch.replace("/", "__")
            subprocess.run(["git", "-C", repo, "worktree", "add", "-q", "-b", branch, str(folder), base], check=True)
            print(json.dumps({"path": str(folder)}))
        ''').lstrip())
        wt.chmod(0o755)
        self.scenario = self.root / "scenario.json"
        self.log = self.root / "calls.json"
        self.environment = patch.dict(os.environ, {
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "LOOP_SCENARIO": str(self.scenario), "LOOP_LOG": str(self.log),
            "LOOP_PUSH": str(self.root / "push"), "LOOP_WT_ROOT": str(self.root / "worktrees"),
            "GOERWIN_CODE_REVIEWS_DIR": str(self.root / "archive"),
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def run_loop(self, *args):
        result = subprocess.run([sys.executable, str(SKILL / "scripts/review_loop.py"), *args, "--cwd", str(self.repo)],
                                capture_output=True, text=True)
        if result.returncode:
            return {"returncode": result.returncode, "stop_reason": None, **json.loads(result.stderr)}
        return json.loads(result.stdout)

    def start(self, reviews, decisions, *extra):
        self.scenario.write_text(json.dumps({"reviews": reviews, "decisions": decisions}))
        return self.run_loop("start", "--reviewer", "sol-high", "--implementer", "opus-high", *extra)

    def calls(self, role):
        return [call for call in json.loads(self.log.read_text()) if call["role"] == role]

    def test_rounds_commit_fixes_carry_decisions_and_stop_when_clean(self):
        task = self.repo / "TASK-pagination.md"
        task.write_text("Keep cursors stable across pages.")
        state = self.start([["Cursor lost", "Rename helper"], ["Off by one"], []],
                           [["applied", "pushed_back"], ["applied"]],
                           "--intent", "Ship pagination", "--intent-file", str(task))
        self.assertEqual((state["status"], state["stop_reason"]), ("squash_pending", "no_findings"))
        self.assertEqual(len(state["rounds"]), 3)
        self.assertIn("code.txt", state["squash_stat"])
        before = self.git("diff", "origin/main", "HEAD")
        state = self.run_loop("squash", "--message", "fix: keep cursors stable across pages")
        self.assertEqual(state["status"], "stopped")
        self.assertEqual(self.git("log", "--format=%s", "origin/main..HEAD").splitlines(),
                         ["fix: keep cursors stable across pages", "feat: pagination"])
        self.assertEqual(self.git("diff", "origin/main", "HEAD"), before)
        self.assertIn("round 1:", self.git("log", "-1", "--format=%b"))
        self.assertEqual(self.run_loop("squash", "--message", "fix: again")["returncode"], 1)
        self.assertEqual(self.git("status", "--porcelain"), "?? TASK-pagination.md")
        reviewers, implementers = self.calls("reviewer"), self.calls("implementer")
        self.assertEqual(reviewers[0]["argv"][0], "exec")
        self.assertEqual(implementers[0]["argv"][:3], ["--model", "claude-opus-5-5", "--effort"])
        self.assertIn("Keep cursors stable", reviewers[0]["prompt"])
        self.assertIn("Ship pagination", implementers[0]["prompt"])
        self.assertIn("pushed_back — pushed_back", reviewers[1]["prompt"])
        self.assertIn("Rename helper", reviewers[1]["prompt"])
        self.assertNotEqual((self.root / "push").read_text(), "0")
        reports = sorted((self.root / "archive/project").glob("*.md"))
        self.assertEqual([path.name for path in reports if "receiving" in path.name],
                         [reports[0].stem + ".receiving.md", reports[2].stem + ".receiving.md"])

    def test_waiting_pauses_and_resume_answers_in_the_same_round(self):
        state = self.start([["Cursor lost", "Filter reset"], []], [["applied", "waiting"], ["applied"]])
        self.assertEqual(state["status"], "waiting")
        self.assertEqual([item["question"] for item in state["questions"]], ["Keep the cursor?"])
        self.assertEqual(self.git("log", "-1", "--format=%s"), "fix: address review round 1")
        self.assertEqual(self.run_loop("resume")["returncode"], 1)
        state = self.run_loop("resume", "--answers", "F2: keep it")
        self.assertEqual(state["stop_reason"], "no_findings")
        self.assertIn("F2: keep it", self.calls("implementer")[1]["prompt"])
        self.assertEqual(self.git("log", "-1", "--format=%s"), "fix: address review round 1 (answers)")
        self.assertEqual(len(self.calls("reviewer")), 2)

    def test_round_limit_and_nothing_applied_stop_the_loop(self):
        state = self.start([["A"], ["B"]], [["applied"], ["applied"]], "--max-rounds", "2", "--rubric", "adversarial")
        self.assertTrue(all("# Rubric: adversarial" in call["prompt"] for call in self.calls("reviewer")))
        self.assertEqual((state["stop_reason"], len(state["rounds"])), ("round_limit", 2))
        self.assertEqual(state["status"], "squash_pending")
        self.git("reset", "-q", "--hard", "HEAD~2")
        self.log.unlink()
        state = self.start([["A"]], [["pushed_back"]])
        self.assertEqual((state["status"], state["stop_reason"]), ("stopped", "nothing_applied"))

    def test_creation_hook_finishes_before_each_reviewer_starts(self):
        wt = self.root / "bin/wt"
        wt.write_text(wt.read_text().replace(
            'print(json.dumps({"path": str(folder)}))',
            '(folder / "SETUP_DONE").write_text("ok")\nprint(json.dumps({"path": str(folder)}))'))
        agent = self.root / "bin/codex"
        agent.write_text(agent.read_text().replace(
            'if role == "reviewer":',
            'if role == "reviewer":\n    assert Path("SETUP_DONE").exists(), "reviewer started before setup"'))
        state = self.start([["A"], []], [["applied"]])
        self.assertEqual(state.get("stop_reason"), "no_findings", state.get("error"))

    def test_dirty_worktree_refuses_to_start(self):
        (self.repo / "code.txt").write_text("my uncommitted work\n")
        result = self.start([[]], [])
        self.assertEqual(result["returncode"], 1)
        self.assertIn("Commit or stash", result["error"])
        self.assertFalse(self.log.exists())

    def test_failed_round_commit_stops_and_can_resume(self):
        hook = self.repo / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result = self.start([["A"], []], [["applied"]])
        self.assertIn("commit failed", result["error"])
        state = loop.loops(None, str(self.repo))[0]
        self.assertEqual((state["stop_reason"], state["rounds"][0]["step"]), ("error", "commit"))
        hook.unlink()
        state = self.run_loop("resume")
        self.assertEqual(state["stop_reason"], "no_findings")
        self.assertEqual(len(self.calls("implementer")), 1)


if __name__ == "__main__":
    unittest.main()
