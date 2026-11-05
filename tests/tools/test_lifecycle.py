import copy
import contextlib
import importlib.machinery
import importlib.util
import json
import os
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_worktrees as fixture
from test_worktrees import BIN, ROOT
from goerwin_tools import herdr_adapter as herdr, processes, removal, runtime, worktrees


def load_command():
    loader = importlib.machinery.SourceFileLoader("worktree_cli", str(BIN / "goerwin-wt"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class LifecycleTests(unittest.TestCase):
    git = fixture.WorktreeTests.git
    switch = fixture.WorktreeTests.switch

    def setUp(self):
        fixture.WorktreeTests.setUp(self)
        self.folder = self.switch("feature", "main")["path"]
        self.ui = {"spaces": []}
        self.records = {}
        self.table = {os.getpid(): self.process(os.getpid(), str(self.repo), name="python")}
        self.events = []
        for mock in (
            patch.object(herdr, "snapshot", side_effect=lambda: copy.deepcopy(self.ui)),
            patch.object(herdr, "sessions", side_effect=lambda: copy.deepcopy(self.records)),
            patch.object(herdr.shutil, "which", return_value="/fake/executable"),
            patch.object(processes, "snapshot", side_effect=lambda: copy.deepcopy(self.table)),
            patch.object(processes, "terminate", side_effect=self.terminate),
            patch.object(herdr, "core", side_effect=self.core),
            patch.object(herdr, "command", side_effect=self.command),
        ):
            mock.start()
            self.addCleanup(mock.stop)
        self.addCleanup(fixture.WorktreeTests.tearDown, self)

    def process(self, pid, cwd, parent=1, name="zsh"):
        return {"pid": pid, "parent": parent, "uid": os.getuid(), "state": "S",
                "started": str(pid), "cwd": cwd, "name": name}

    def add_space(self, name="space", *, agent=False, mixed=False):
        address = "t-" + name
        pid = 10000 + len(self.table)
        record = {"address": address, "pid": pid, "state": "live", "cwd": self.folder,
                  "foreground": {"cwd": self.folder}, "status": {"state": "idle"} if agent else None,
                  "reported": agent, "labels": {"herdr.space": name}, "parent": None}
        self.records[address] = record
        self.table[pid] = self.process(pid, self.folder)
        tab = {"id": "tab-" + name, "terminals": [{"terminal": address}]}
        space = {"id": name, "folder": self.folder, "machine": None, "tabs": [tab]}
        self.ui["spaces"].append(space)
        if mixed:
            other = "other-" + name
            self.records[other] = {**record, "address": other, "pid": pid + 1000,
                                   "cwd": str(self.repo), "foreground": {"cwd": str(self.repo)}}
            self.table[pid + 1000] = self.process(pid + 1000, str(self.repo))
            tab["terminals"].append({"terminal": other})
        return address

    def terminate(self, items):
        self.events.append(("terminate", [item["pid"] for item in items]))
        for item in items:
            self.table.pop(item["pid"], None)

    def core(self, args, **kwargs):
        action, address = args[:2]
        self.events.append((action, address))
        if action == "get":
            return self.records.get(address, {"state": "finished"})
        if action == "kill":
            record = self.records.pop(address)
            self.table.pop(record["pid"], None)
            self.ui["spaces"] = [space for space in self.ui["spaces"]
                                  if space["id"] != record["labels"]["herdr.space"]]
        return {}

    def command(self, args):
        self.events.append(("close", args))
        target = json.loads(args[-1])["id"]
        for address, record in list(self.records.items()):
            if record["labels"]["herdr.space"] == target:
                self.records.pop(address)
                self.table.pop(record["pid"], None)
        self.ui["spaces"] = [space for space in self.ui["spaces"] if space["id"] != target]
        return {}

    def remove(self, **kwargs):
        return removal.remove("feature", str(self.repo), caller=str(self.repo), **kwargs)

    def remove_calls(self):
        return [args for args in map(json.loads, self.log.read_text().splitlines()) if "remove" in args]

    def test_removes_checkout_preserves_branch_and_cleans_duplicate_spaces(self):
        self.add_space("one")
        self.add_space("two")
        result = self.remove()
        self.assertFalse(Path(self.folder).exists())
        self.assertEqual(self.git("show-ref", "--verify", "refs/heads/feature").split()[0], self.base)
        self.assertEqual(result["closed_spaces"], ["one", "two"])
        self.assertEqual(result["status"], "removed")
        args = self.remove_calls()[0]
        self.assertIn("--foreground", args)
        self.assertIn("--no-delete-branch", args)
        self.assertNotIn("--reap", args)

    def test_even_idle_agent_requires_explicit_stop(self):
        self.add_space(agent=True)
        with self.assertRaisesRegex(runtime.CommandError, "--stop"):
            self.remove()
        self.assertTrue(Path(self.folder).exists())
        self.assertEqual(self.events, [])
        self.assertEqual(self.remove_calls(), [])

    def test_stop_interrupts_then_ends_only_target_agent(self):
        address = self.add_space(agent=True)
        self.table[9999] = self.process(9999, str(self.repo), name="unrelated-server")
        result = self.remove(stop_work=True)
        self.assertEqual(self.events[:4], [("get", address), ("interrupt", address), ("get", address), ("kill", address)])
        self.assertIn(9999, self.table)
        self.assertEqual(result["stopped_terminals"], [address])

    def test_detached_job_requires_stop_and_is_terminated(self):
        self.table[9000] = self.process(9000, self.folder, name="watcher")
        with self.assertRaisesRegex(runtime.CommandError, "--stop"):
            self.remove()
        result = self.remove(stop_work=True)
        self.assertIn(9000, result["stopped_processes"])
        self.assertNotIn(9000, self.table)

    def test_force_does_not_authorize_stopping_agent(self):
        self.add_space(agent=True)
        (Path(self.folder) / "dirty").write_text("personal work")
        with self.assertRaisesRegex(runtime.CommandError, "dirty"):
            self.remove(stop_work=True)
        self.assertEqual(self.events, [])
        with self.assertRaisesRegex(runtime.CommandError, "--stop"):
            self.remove(force=True)
        self.remove(force=True, stop_work=True)
        self.assertIn("--force", self.remove_calls()[0])

    def test_main_and_caller_protection(self):
        for target, caller in (("main", str(self.repo)), ("feature", self.folder)):
            with self.assertRaises(runtime.CommandError):
                removal.remove(target, str(self.repo), caller=caller, force=True, stop_work=True)
        self.assertEqual(self.events, [])
        self.assertTrue(Path(self.folder).exists())

    def test_lock_blocks_before_stopping(self):
        self.add_space(agent=True)
        self.git("worktree", "lock", self.folder)
        with self.assertRaisesRegex(runtime.CommandError, "locked"):
            self.remove(stop_work=True, force=True)
        self.assertEqual(self.events, [])

    def test_detached_unretained_commit_is_protected(self):
        self.git("checkout", "--detach", cwd=self.folder)
        self.git("commit", "--allow-empty", "-m", "detached work", cwd=self.folder)
        with self.assertRaisesRegex(runtime.CommandError, "retaining branch"):
            removal.remove(self.folder, str(self.repo), caller=str(self.repo), force=True, stop_work=True)
        self.assertTrue(Path(self.folder).exists())
        self.assertEqual(self.events, [])

    def test_mixed_space_blocks_without_any_shutdown(self):
        self.add_space(agent=True, mixed=True)
        with self.assertRaisesRegex(herdr.AdapterError, "unrelated"):
            self.remove(stop_work=True)
        self.assertEqual(self.events, [])
        self.assertEqual(self.remove_calls(), [])

    def test_wt_failure_reports_stopped_sessions_but_preserves_checkout(self):
        address = self.add_space(agent=True)
        with patch.dict(os.environ, WTS_TEST_REMOVE_FAIL="1"):
            with self.assertRaises(removal.RemovalError) as raised:
                self.remove(stop_work=True)
        result = raised.exception.result
        self.assertFalse(result["worktree_removed"])
        self.assertEqual(result["stopped_terminals"], [address])
        self.assertEqual(json.loads(Path(result["receipt"]).read_text())["status"], "partial")
        self.assertTrue(Path(self.folder).is_dir())

    def test_cleanup_failure_is_retried_without_repeating_deletion(self):
        self.add_space()
        with patch.object(herdr, "command", side_effect=herdr.AdapterError("unavailable")):
            with self.assertRaises(removal.RemovalError) as raised:
                self.remove()
        self.assertTrue(raised.exception.result["worktree_removed"])
        self.assertFalse(Path(self.folder).exists())
        result = self.remove()
        self.assertEqual(result["status"], "removed")
        self.assertFalse(result["cleanup_pending"])
        self.assertEqual(len(self.remove_calls()), 1)

    def test_cleanup_retry_refuses_recreated_directory(self):
        self.add_space()
        with patch.object(herdr, "command", side_effect=herdr.AdapterError("unavailable")):
            with self.assertRaises(removal.RemovalError):
                self.remove()
        Path(self.folder).mkdir()
        (Path(self.folder) / "keep").write_text("new work")
        with self.assertRaisesRegex(removal.RemovalError, "path still exists"):
            self.remove()
        self.assertEqual((Path(self.folder) / "keep").read_text(), "new work")
        self.assertEqual(len(self.remove_calls()), 1)

    def test_receipt_write_failure_still_reports_completed_deletion_and_can_recover(self):
        self.add_space()
        def save(path, result):
            if result.get("worktree_removed"):
                raise OSError("disk full")
            runtime.json_write(path, result)
        with patch.object(removal, "json_write", side_effect=save):
            with self.assertRaises(removal.RemovalError) as raised:
                self.remove()
        self.assertTrue(raised.exception.result["worktree_removed"])
        self.assertEqual(raised.exception.result["receipt_error"], "disk full")
        self.assertEqual(self.remove()["status"], "removed")
        self.assertEqual(len(self.remove_calls()), 1)

    def test_shutdown_that_cannot_be_verified_prevents_deletion(self):
        self.add_space(agent=True)
        with patch.object(herdr, "core", return_value=copy.deepcopy(self.records["t-space"])):
            with patch.object(processes, "terminate"):
                with self.assertRaisesRegex(removal.RemovalError, "Shutdown could not be verified"):
                    self.remove(stop_work=True)
        self.assertTrue(Path(self.folder).is_dir())
        self.assertEqual(self.remove_calls(), [])

    def test_replaced_core_terminal_is_never_interrupted_or_killed(self):
        address = self.add_space(agent=True)
        changed = {**self.records[address], "pid": 55555}
        with patch.object(herdr, "core", return_value=changed) as core:
            with self.assertRaisesRegex(removal.RemovalError, "was replaced"):
                self.remove(stop_work=True)
        self.assertEqual([call.args[0][0] for call in core.call_args_list], ["get"])
        self.assertTrue(Path(self.folder).exists())

    def test_worker_that_moves_during_interrupt_is_not_killed(self):
        address = self.add_space(agent=True)
        before = self.records[address]
        after = {**before, "foreground": {"cwd": str(self.repo)}}
        with patch.object(herdr, "core", side_effect=[before, {}, after]) as core:
            with self.assertRaisesRegex(removal.RemovalError, "unrelated"):
                self.remove(stop_work=True)
        self.assertEqual([call.args[0][0] for call in core.call_args_list], ["get", "interrupt", "get"])
        self.assertTrue(Path(self.folder).exists())

    def test_current_directory_overrides_stale_space_folder(self):
        self.add_space()
        self.ui["spaces"][0]["folder"] = str(self.repo)
        state = herdr.presentation()
        self.assertEqual(herdr.local_space(state, self.folder)["id"], "space")
        self.assertIsNone(herdr.local_space(state, str(self.repo)))
        self.assertEqual(self.remove()["closed_spaces"], ["space"])

    def test_cli_focus_requires_herdr_and_missing_remove_target_is_error(self):
        for args in (("switch", "feature", "--focus"), ("remove",)):
            result = subprocess.run([sys.executable, str(BIN / "goerwin-wt"), *args],
                                    cwd=self.repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
        self.assertEqual(self.events, [])

    def test_existing_path_switch_reuses_linked_checkout(self):
        result = self.switch(self.folder)
        self.assertEqual(result["path"], self.folder)
        self.assertTrue(result["reused"])

    def test_directory_named_like_branch_does_not_select_main_checkout(self):
        (self.repo / "feature").mkdir()
        result = self.switch("feature")
        self.assertEqual(result["path"], self.folder)

    def test_cleanup_handles_getcwd_failure_for_identical_idle_terminal(self):
        address = self.add_space()
        self.ui["spaces"][0]["folder"] = str(self.repo)
        self.records[address]["cwd"] = str(self.repo)  # Original launch directory is stale.
        def sessions():
            records = copy.deepcopy(self.records)
            if not Path(self.folder).exists() and address in records:
                records[address]["foreground"] = {}  # Deleted cwd cannot be read.
            return records
        with patch.object(herdr, "sessions", side_effect=sessions):
            self.assertEqual(self.remove()["closed_spaces"], ["space"])

    def test_cleanup_does_not_close_session_that_changed_to_unrelated_directory(self):
        address = self.add_space()
        def sessions():
            records = copy.deepcopy(self.records)
            if not Path(self.folder).exists() and address in records:
                records[address]["foreground"] = {"cwd": str(self.repo)}
            return records
        with patch.object(herdr, "sessions", side_effect=sessions):
            with self.assertRaisesRegex(removal.RemovalError, "unrelated"):
                self.remove()
        self.assertEqual(self.events, [])


class ProcessSafetyTests(unittest.TestCase):
    def test_caller_ancestor_is_protected_even_when_directory_changed(self):
        table = {os.getpid(): {"parent": 101, "cwd": "/other", "state": "S"},
                 101: {"parent": 1, "cwd": "/target", "state": "S"}}
        with self.assertRaisesRegex(runtime.CommandError, "invoking"):
            processes.associated(table, "/target")

    def test_recycled_pid_is_never_signalled(self):
        item = {"pid": 1234, "started": "old", "state": "S"}
        with patch.object(processes, "snapshot", return_value={1234: {**item, "started": "new"}}):
            with patch.object(processes.os, "kill") as kill:
                with self.assertRaisesRegex(runtime.CommandError, "identity"):
                    processes.signal_process(item, 15)
        kill.assert_not_called()

    def test_nested_worktree_is_not_owned_by_outer_checkout(self):
        table = {999: {"parent": 1, "cwd": "/repo/nested", "state": "S"}}
        self.assertEqual(processes.associated(table, "/repo", worktree_paths=["/repo", "/repo/nested"]), {})


class PresentationTests(unittest.TestCase):
    def test_list_herdr_is_additive_idempotent_and_preserves_focus_without_agents(self):
        cli = load_command()
        with tempfile.TemporaryDirectory() as directory:
            folders = [Path(directory) / name for name in ("main", "feature")]
            for folder in folders:
                folder.mkdir()
            listing = {"schema": 2, "repo": {}, "items": [
                {"branch": folder.name, "worktree": {"path": str(folder)}} for folder in folders]}
            state = {"spaces": [{"id": "original", "folder": "/unrelated", "active": True,
                                   "tabs": [{"id": "original-tab", "active": True}]}]}
            actions = []

            def command(args):
                actions.append(args)
                if args[1] == "space.new":
                    name = args[args.index("--name") + 1]
                    for space in state["spaces"]:
                        space["active"] = False
                    state["spaces"].append({"id": name, "folder": args[args.index("--folder") + 1],
                                             "active": True, "tabs": [{"id": name + "-tab", "active": True}]})
                    return {"space": name, "tab": name + "-tab"}
                self.assertEqual(args[1], "tab.select")
                for space in state["spaces"]:
                    space["active"] = any(tab["id"] == args[-1] for tab in space["tabs"])
                return {}

            with patch.object(worktrees, "listing", return_value=listing), \
                 patch.object(herdr, "presentation", side_effect=lambda: copy.deepcopy(state)), \
                 patch.object(herdr, "command", side_effect=command), \
                 patch.object(herdr, "raise_app") as raise_app:
                for _ in range(2):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(cli.main(["list", "--herdr", "--json"]), 0)
            self.assertEqual(len([args for args in actions if args[1] == "space.new"]), 2)
            self.assertTrue(state["spaces"][0]["active"])
            self.assertEqual(len(state["spaces"]), 3)
            self.assertFalse(any("--argv" in args or "--task" in args for args in actions))
            raise_app.assert_not_called()

    def test_requested_ui_failure_reports_created_checkout_and_nonzero(self):
        cli = load_command()
        stdout = io.StringIO()
        with patch.object(worktrees, "switch", return_value={"path": "/checkout", "branch": "feature"}), \
             patch.object(herdr, "presentation", side_effect=herdr.AdapterError("not reachable")), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["switch", "feature", "--herdr", "--json"])
        self.assertEqual(code, 1)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["path"], "/checkout")
        self.assertEqual(result["status"], "partial")
