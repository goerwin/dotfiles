"""Herdr's tab API; independent of target resolution and model selection."""

import json
import os
import shutil
import subprocess
from . import processes
from .runtime import CommandError, toplevel


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
        data = json.loads(result.stdout)
        if isinstance(data, dict) and data.get("error"):
            raise AdapterError(str(data["error"]))
        return data
    except ValueError as error:
        raise AdapterError("Herdr returned invalid JSON") from error


def snapshot():
    return command(["ls"])


def local_space(state, folder):
    return next((item for item in state.get("spaces", []) if (
        not item.get("machine") and (item.get("current_folder") or item.get("folder"))
        and os.path.realpath(item.get("current_folder") or item["folder"]) == folder
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


def focus_worktree(worktree, name, focus=True, state=None):
    """Make sure the worktree has a Herdr tab; with focus, also select it and raise Herdr."""
    folder = os.path.realpath(worktree)
    state = snapshot() if state is None else state
    space = local_space(state, folder)
    tabs = space.get("tabs", []) if space else []
    tab = next((item for item in tabs if item.get("active")), tabs[0] if tabs else None)
    warnings = []
    if tab and not focus:
        return {"available": True, "space": space["id"], "tab": tab["id"], "warnings": warnings}
    if tab:
        result = command(["do", "tab.select", "--id", tab["id"]])
        result = {"space": space["id"], "tab": tab["id"], **result}
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


def core(args, timeout=30):
    try:
        result = subprocess.run(["hc", *args, "--json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AdapterError(str(error)) from error
    if result.returncode:
        raise AdapterError(result.stderr.strip() or "Herdr core command failed")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise AdapterError("Herdr core returned invalid JSON") from error


def sessions():
    """Inspect local terminals, including agents without visible panes."""
    if not shutil.which("hc"):
        return {}
    data = core(["ls"])
    rows = data.get("terminals") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise AdapterError("Herdr core omitted its terminal list")
    records = {}
    for row in rows:
        address = row.get("address")
        if not isinstance(address, str):
            raise AdapterError("Herdr core omitted a terminal address")
        if "/" in address or row.get("state") == "finished":
            continue
        record = core(["get", address])
        if record.get("address") != address:
            raise AdapterError("Herdr returned an unexpected terminal")
        records[address] = record
    return records


def current_folder(record):
    return (record.get("foreground") or {}).get("cwd") or record.get("cwd")


def presentation():
    """Refresh stale space folders from their first terminal, as Herdr's sidebar does."""
    state, records = snapshot(), sessions()
    for space in state.get("spaces", []):
        if space.get("machine"):
            continue
        first = next((term for tab in space.get("tabs", []) for term in tab.get("terminals", [])), None)
        if first and first["terminal"] in records:
            folder = current_folder(records[first["terminal"]])
            try:
                space["current_folder"] = toplevel(folder) if folder else None
            except CommandError:
                space["current_folder"] = folder
    return state


def inspect_worktree(folder, worktree_paths, terminal_locations=None, process_table=None):
    """Find every associated space and refuse mixed or uninspectable contents."""
    installed = shutil.which("herdr-app")
    if installed and not shutil.which("hc"):
        raise AdapterError("Herdr is installed but hc is unavailable; cannot verify its sessions")
    state = snapshot() if installed else {"spaces": []}
    records = sessions()

    def location(address, record):
        foreground = record.get("foreground") or {}
        current = foreground.get("cwd")
        if current:
            return current
        observed = (process_table or {}).get(foreground.get("pid") or record.get("pid"), {}).get("cwd")
        if observed and os.path.isdir(observed):
            return observed
        # getcwd can fail after deletion. A remembered cwd is usable only for
        # the exact terminal process inspected before deletion, never a new PID.
        old = (terminal_locations or {}).get(address, {})
        item = (process_table or {}).get(record.get("pid"), {})
        if (old.get("pid") == record.get("pid") and old.get("started")
                and old["started"] == item.get("started")):
            return old["folder"]
        return record.get("cwd")

    def belongs(path):
        matches = [os.path.realpath(p) for p in worktree_paths if processes.inside(path, p)]
        return bool(matches) and max(matches, key=len) == folder

    spaces, addresses = [], set()
    for space in state.get("spaces", []):
        if space.get("machine"):
            continue
        visible = {term["terminal"] for tab in space.get("tabs", []) for term in tab.get("terminals", [])}
        attached = visible | {address for address, record in records.items()
                              if record.get("labels", {}).get("herdr.space") == space["id"]}
        target_records = [(address, records[address]) for address in attached if address in records]
        if not (os.path.realpath(space.get("folder") or "/") == folder
                or any(belongs(location(address, record)) for address, record in target_records)):
            continue
        # A mod-only pane/tab is not attributable from the terminal snapshot.
        if any(not tab.get("terminals") for tab in space.get("tabs", [])):
            raise AdapterError(f"Space {space['id']} has non-terminal tabs; reorganize it before removal")
        for address in attached:
            record = records.get(address)
            if record is None:
                raise AdapterError(f"Cannot inspect terminal {address} in space {space['id']}")
            if record.get("state") == "finished":
                continue
            if not belongs(location(address, record)):
                raise AdapterError(f"Space {space['id']} contains unrelated work in {address}; move it before removal")
        spaces.append(space["id"])
        addresses.update(attached)
    addresses.update(address for address, record in records.items() if belongs(location(address, record)))
    # Include core children whose cwd has changed: they still belong to the worker.
    while True:
        children = {address for address, record in records.items()
                    if record.get("parent") in addresses} - addresses
        if not children:
            break
        addresses.update(children)
    selected = {address: records[address] for address in addresses if address in records}
    if any(record.get("state") != "live" or not isinstance(record.get("pid"), int)
           for record in selected.values()):
        raise AdapterError("Terminal process metadata is incomplete; refusing removal")
    return {"spaces": spaces, "terminals": selected, "state": state}
