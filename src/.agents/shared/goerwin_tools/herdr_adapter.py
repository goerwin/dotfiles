"""Herdr's tab API; independent of target resolution and model selection."""

import json
import os
import subprocess
from pathlib import Path


class AdapterError(RuntimeError):
    pass


def command(args):
    try:
        result = subprocess.run(
            ["herdr-app", *args], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AdapterError(str(error)) from error
    if result.returncode:
        raise AdapterError(result.stderr.strip() or "Herdr command failed")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise AdapterError("Herdr returned invalid JSON") from error


def snapshot():
    return command(["ls"])


def focus_worktree(worktree, name):
    state = snapshot()
    folder = os.path.realpath(worktree)
    space = next((item for item in state.get("spaces", []) if (
        not item.get("machine") and item.get("folder")
        and os.path.realpath(item["folder"]) == folder
    )), None)
    if space:
        tabs = space.get("tabs", [])
        tab = next((item for item in tabs if item.get("active")), tabs[0] if tabs else None)
        if tab:
            result = command(["do", "tab.select", "--id", tab["id"]])
            terminals = tab.get("terminals", [])
            if terminals:
                command(["do", "pane.focus", "--terminal", terminals[0]["terminal"]])
        else:
            result = command(["do", "tab.new", "--space", space["id"], "--name", name, "--folder", folder])
    else:
        result = command(["do", "space.new", "--name", name, "--folder", folder, "--tab", name])
    raised = subprocess.run(["herdr-app"], capture_output=True, text=True, timeout=15)
    if raised.returncode:
        return {"available": True, **result, "warning": raised.stderr.strip() or "Could not raise Herdr"}
    return {"available": True, **result}


def open_review(worktree, name, argv, task, state=None):
    state = snapshot() if state is None else state
    folder = os.path.realpath(worktree)
    space = next(
        (
            item
            for item in state.get("spaces", [])
            if not item.get("machine")
            and item.get("folder")
            and os.path.realpath(item["folder"]) == folder
        ),
        None,
    )
    args = (
        ["tab.new", "--space", space["id"], "--name", name]
        if space
        else ["space.new", "--tab", name]
    )
    result = command(
        [
            "do",
            *args,
            "--folder",
            str(Path(worktree)),
            "--argv",
            json.dumps(argv),
            "--task",
            task,
        ]
    )
    # Creation selects the new tab. Focus failures must not spawn a second agent.
    warnings = []
    if result.get("terminal"):
        try:
            command(["do", "pane.focus", "--terminal", result["terminal"]])
        except AdapterError as error:
            warnings.append(str(error))
    elif result.get("tab"):
        try:
            command(["do", "tab.select", "--id", result["tab"]])
        except AdapterError as error:
            warnings.append(str(error))
    try:
        raised = subprocess.run(
            ["herdr-app"], capture_output=True, text=True, timeout=15
        )
        if raised.returncode:
            warnings.append(raised.stderr.strip() or "Could not raise Herdr")
    except subprocess.TimeoutExpired:
        warnings.append("Herdr foreground activation timed out")
    return {**result, "warnings": warnings}
