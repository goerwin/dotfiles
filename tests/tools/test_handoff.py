import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from test_worktrees import ROOT

SCRIPT = ROOT / "src/.agents/skills/goerwin-handoff/scripts/launch.py"
spec = importlib.util.spec_from_file_location("handoff_launcher", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="handoff-tests-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.folder = self.root / "checkout"
        self.folder.mkdir()
        self.task = self.root / "task.md"
        self.task.write_text("Implement the authorized change. Preserve existing work.")
        self.args = argparse.Namespace(target="feature", base=None, cwd=self.root, task_file=self.task,
                                       model="gpt-6.1-sol", effort="high", tab_name=None)
        self.created = []
        self.commands = []
        self.latest = None
        self.state = {"spaces": [{"id": "space", "folder": str(self.folder), "tabs": [
            {"id": "existing-user-tab", "active": True, "terminals": [{"terminal": "existing-agent"}]}]}]}

    def fake_run(self, argv, **kwargs):
        self.commands.append(argv)
        if argv[:2] == ["goerwin-wt", "switch"]:
            return {"path": str(self.folder), "branch": "feature", "reused": True}
        if argv[:2] == ["herdr-app", "status"]:
            return {"tab": self.latest["tab"], "agent": self.latest["terminal"]}
        if argv[:2] == ["hc", "get"]:
            return {"state": "live", "parent": None, "die_with_parent": False, "status": {"state": "idle"},
                    "foreground": {"name": "codex", "cwd": str(self.folder), "argv": [
                        "codex", "--no-daemon", "--model", self.args.model,
                        "-c", "model_reasoning_effort=" + json.dumps(self.args.effort)]}}
        return copy.deepcopy(self.state)

    def app(self, action, parameters):
        if action == "tab.new":
            self.created.append(parameters)
            count = len(self.created)
            self.latest = {"space": "space", "tab": f"new-tab-{count}", "terminal": f"new-agent-{count}"}
            return dict(self.latest)
        self.assertIn(action, ("tab.select", "pane.focus"))
        self.assertNotIn("existing-user-tab", parameters.values())
        self.assertNotIn("existing-agent", parameters.values())
        return {}

    def test_each_handoff_creates_fresh_visible_agent_and_transfers_context(self):
        with patch.object(launcher.shutil, "which", return_value="/fake/command"), \
             patch.object(launcher, "run", side_effect=self.fake_run), \
             patch.object(launcher, "app", side_effect=self.app), \
             patch.object(launcher.herdr_adapter, "presentation", return_value=self.state):
            for number in range(2):
                receipt = {}
                launcher.launch(self.args, self.root / f"receipt-{number}.json", receipt)
                self.assertTrue(receipt["agent_started"])
                self.assertTrue(receipt["focused"])
                self.assertTrue(receipt["independent_session"])
        self.assertEqual(len(self.created), 2)
        self.assertTrue(all(parameters["space"] == "space" for parameters in self.created))
        self.assertTrue(all(parameters["task"] == self.task.read_text() for parameters in self.created))
        switches = [command for command in self.commands if command[0] == "goerwin-wt"]
        self.assertEqual(switches, [["goerwin-wt", "switch", "feature", "-C", str(self.root), "--json"]] * 2)

    def test_uncertain_launch_records_state_and_never_retries(self):
        receipt = {}
        def fail(action, parameters):
            if action == "tab.new":
                self.created.append(parameters)
                raise RuntimeError("request timed out after dispatch")
            return {}
        with patch.object(launcher.shutil, "which", return_value="/fake/command"), \
             patch.object(launcher, "run", side_effect=self.fake_run), \
             patch.object(launcher, "app", side_effect=fail), \
             patch.object(launcher.herdr_adapter, "presentation", return_value=self.state):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                launcher.launch(self.args, self.root / "receipt.json", receipt)
        self.assertEqual(len(self.created), 1)
        self.assertEqual(json.loads((self.root / "receipt.json").read_text())["status"], "launching")

    def test_existing_path_launches_fresh_session_via_cli_switch(self):
        self.args.target = str(self.folder)
        with patch.object(launcher.shutil, "which", return_value="/fake/command"), \
             patch.object(launcher, "run", side_effect=self.fake_run), \
             patch.object(launcher, "app", side_effect=self.app), \
             patch.object(launcher.herdr_adapter, "presentation", return_value=self.state):
            launcher.launch(self.args, self.root / "receipt.json", {})
        self.assertIn(["goerwin-wt", "switch", str(self.folder), "-C", str(self.folder), "--json"], self.commands)
        self.assertEqual(len(self.created), 1)

    def test_structural_launch_does_not_inherit_source_terminal(self):
        with patch.dict(os.environ, HC_TERMINAL_ID="origin-agent"), \
             patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "{}", "")) as run:
            launcher.run(["herdr-app", "do", "tab.new", "{}"], as_json=True)
        self.assertNotIn("HC_TERMINAL_ID", run.call_args.kwargs["env"])
