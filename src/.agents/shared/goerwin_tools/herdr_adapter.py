"""Herdr's tab API; independent of target resolution and model selection."""

import json
import os
import subprocess


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


def local_space(state, folder):
    return next((item for item in state.get("spaces", []) if (
        not item.get("machine") and item.get("folder")
        and os.path.realpath(item["folder"]) == folder
    )), None)


def attempt(warnings, args):
    try:
        command(args)
    except AdapterError as error:
        warnings.append(str(error))


def raise_app(warnings):
    try:
        raised = subprocess.run(["herdr-app"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as error:
        warnings.append(f"Could not raise Herdr: {error}")
        return
    if raised.returncode:
        warnings.append(raised.stderr.strip() or "Could not raise Herdr")


def focus_worktree(worktree, name, focus=True):
    """Make sure the worktree has a Herdr tab; with focus, also select it and raise Herdr."""
    folder = os.path.realpath(worktree)
    state = snapshot()
    space = local_space(state, folder)
    tabs = space.get("tabs", []) if space else []
    tab = next((item for item in tabs if item.get("active")), tabs[0] if tabs else None)
    warnings = []
    if tab and not focus:
        return {"available": True, "tab": tab["id"], "warnings": warnings}
    if tab:
        result = command(["do", "tab.select", "--id", tab["id"]])
        if tab.get("terminals"):
            attempt(warnings, ["do", "pane.focus", "--terminal", tab["terminals"][0]["terminal"]])
    else:
        result = command(
            ["do", "tab.new", "--space", space["id"], "--name", name, "--folder", folder] if space
            else ["do", "space.new", "--name", name, "--folder", folder, "--tab", name]
        )
        if not focus:
            restore(state, warnings)
            return {"available": True, **result, "warnings": warnings}
    raise_app(warnings)
    return {"available": True, **result, "warnings": warnings}


def restore(state, warnings):
    """Reselect the tab that was active before; creating a tab selects it."""
    active = next((
        tab for space in state.get("spaces", []) if space.get("active")
        for tab in space.get("tabs", []) if tab.get("active")
    ), None)
    if active:
        attempt(warnings, ["do", "tab.select", "--id", active["id"]])


def open_review(worktree, name, argv, task, state):
    space = local_space(state, os.path.realpath(worktree))
    target = ["tab.new", "--space", space["id"], "--name", name] if space else ["space.new", "--tab", name]
    result = command([
        "do", *target, "--folder", str(worktree), "--argv", json.dumps(argv), "--task", task,
    ])
    # Creation selects the new tab. Focus failures must not spawn a second agent.
    warnings = []
    if result.get("terminal"):
        attempt(warnings, ["do", "pane.focus", "--terminal", result["terminal"]])
    elif result.get("tab"):
        attempt(warnings, ["do", "tab.select", "--id", result["tab"]])
    raise_app(warnings)
    return {**result, "warnings": warnings}
