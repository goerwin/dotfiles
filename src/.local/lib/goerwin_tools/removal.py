"""Coordinate explicit process shutdown, Worktrunk removal, and Herdr cleanup."""

import hashlib
import json
import os
from pathlib import Path

from . import herdr_adapter as herdr, processes, worktrees
from .runtime import (
    CommandError, allocation_lock, common_dir, git, json_read, json_write, now, run, source_root,
)


class RemovalError(CommandError):
    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


def failure(result, error, save):
    result.update(status="partial", error=str(error))
    try:
        save()
    except OSError as persistence_error:
        result["receipt_error"] = str(persistence_error)
    return RemovalError(str(error), result)


def roots(inventory):
    return {record["pid"] for record in inventory["terminals"].values()}


def same_terminal(current, original):
    return (current.get("pid") == original["pid"]
            and current.get("created_ms") == original.get("created_ms"))


def verify_terminal(current, original, address, folder, paths):
    if not same_terminal(current, original):
        raise CommandError(f"Terminal {address} was replaced; refusing shutdown")
    cwd = (current.get("foreground") or {}).get("cwd")
    matches = [path for path in paths if processes.inside(cwd, path)]
    if cwd and (not matches or max(matches, key=len) != folder):
        raise CommandError(f"Terminal {address} moved to unrelated work; refusing shutdown")


def inspect(folder, paths, remembered=None):
    table = processes.snapshot()
    inventory = herdr.inspect_worktree(folder, paths, terminal_locations=remembered, process_table=table)
    selected = processes.associated(table, folder, roots(inventory), paths)
    busy = []
    for address, record in inventory["terminals"].items():
        item = table.get(record["pid"])
        status = record.get("status")
        agent = bool(record.get("reported") or status)
        if item is None or not processes.alive(item):
            raise CommandError(f"Cannot inspect the process of terminal {address}")
        if agent or not processes.idle_shell(item, table):
            busy.append(address)
    terminal_pids = roots(inventory)
    busy.extend(f"pid:{pid}" for pid, item in selected.items()
                if pid not in terminal_pids and not processes.idle_shell(item, table))
    return inventory, selected, busy


def stop(folder, paths, inventory, selected, result, save):
    """Record each attempted shutdown before doing it; never assume an interrupt exits."""
    result["status"] = "stopping"
    save()
    for address in inventory["terminals"]:
        result["stop_attempted"].append(address)
        save()
        # An idle shell can remain until successful deletion closes its space.
        table = processes.snapshot()
        record = inventory["terminals"][address]
        item = table.get(record["pid"])
        if not item or (not record.get("status") and not record.get("reported")
                        and processes.idle_shell(item, table)):
            continue
        if item["started"] != selected[record["pid"]]["started"]:
            raise CommandError(f"Terminal {address} changed process identity; refusing shutdown")
        current = herdr.core(["get", address])
        if current.get("state") == "finished":
            continue
        verify_terminal(current, record, address, folder, paths)
        herdr.core(["interrupt", address, "--timeout", "3"], timeout=10)
        # Interrupt stops a turn, not necessarily the agent process. End this
        # explicitly authorized terminal; core applies hangup and escalation.
        current = herdr.core(["get", address])
        if current.get("state") == "live":
            verify_terminal(current, record, address, folder, paths)
            latest = processes.snapshot()
            item = latest.get(record["pid"])
            if item and item["started"] != selected[record["pid"]]["started"]:
                raise CommandError(f"Terminal {address} changed process identity during shutdown")
            if not (item and not current.get("status") and not current.get("reported")
                    and processes.idle_shell(item, latest)):
                herdr.core(["kill", address], timeout=30)
        result["stopped_terminals"].append(address)
        save()
    # Catch detached jobs and children that outlived their terminal. Include the
    # original snapshot so reparenting or a cwd change cannot hide them.
    table = processes.snapshot()
    remaining = processes.associated(table, folder, (), paths)
    for pid, item in selected.items():
        current = table.get(pid)
        if current and current["started"] == item["started"] and processes.alive(current):
            remaining[pid] = current
    idle_pids = {record["pid"] for record in inventory["terminals"].values()
                 if not record.get("status") and not record.get("reported")}
    targets = [item for pid, item in remaining.items()
               if not (pid in idle_pids and processes.idle_shell(item, table))]
    result["process_stop_attempted"] = [item["pid"] for item in targets]
    save()
    processes.terminate(targets)
    result["stopped_processes"] = result["process_stop_attempted"]
    save()


def preflight(item, repo, caller, force):
    tree = item["worktree"]
    folder = os.path.realpath(tree["path"])
    if tree.get("main") or folder == source_root(repo):
        raise CommandError("The main checkout cannot be removed")
    if processes.inside(caller, folder):
        raise CommandError("Remove the caller's worktree from another checkout/session")
    if "locked" in tree:
        raise CommandError("The worktree is locked; unlock it explicitly first")
    if tree.get("operation"):
        raise CommandError("A Git operation is in progress; finish it before removal")
    if not item.get("branch") and Path(folder).exists():
        preserved = git(folder, "for-each-ref", "--contains=HEAD", "--format=%(refname)", "refs/heads/").stdout.strip()
        if not preserved:
            raise CommandError("Detached commits have no retaining branch; create one before removal")
    changes = tree.get("changes")
    if not force and Path(folder).exists():
        if changes is None:
            raise CommandError("Worktrunk could not determine worktree cleanliness")
        if any(changes.get(key) for key in ("staged", "modified", "untracked", "renamed", "deleted", "conflicted")):
            raise CommandError("The worktree is dirty; --force explicitly permits discarding files")
    return folder


def cleanup(result, paths, save):
    """Only close spaces still wholly attributable to this removed checkout."""
    folder = result["path"]
    if Path(folder).exists():
        raise CommandError("The checkout path exists again; refusing stale cleanup")
    inventory, _, busy = inspect(folder, paths, result.get("terminal_locations"))
    if busy:
        raise CommandError("Worktree removed, but new/live work blocks Herdr cleanup: " + ", ".join(busy))
    remaining = set(result["spaces"]) | set(inventory["spaces"])
    existing = {space["id"] for space in inventory["state"].get("spaces", [])}
    # IDs remembered in the journal must not now identify unrelated spaces.
    if (remaining & existing) - set(inventory["spaces"]):
        raise CommandError("A former Herdr space now contains unrelated work; refusing to close it")
    for space in sorted(remaining & existing):
        # Reinspect between closes: space.close is destructive, not a vetoable request.
        current, _, busy = inspect(folder, paths, result.get("terminal_locations"))
        if busy or space not in current["spaces"]:
            raise CommandError("Herdr changed during cleanup; retry after inspecting its spaces")
        result["space_close_attempted"].append(space)
        save()
        herdr.command(["do", "space.close", json.dumps({"id": space, "confirmed": True})])
        result["closed_spaces"].append(space)
        save()
    final, _, busy = inspect(folder, paths, result.get("terminal_locations"))
    if final["spaces"] or busy:
        raise CommandError("Herdr cleanup is not yet confirmed; retry the same target")
    result.pop("error", None)
    result.update(status="removed", cleanup_pending=False)
    save()


def remove(target, cwd, *, caller=None, stop_work=False, force=False, no_hooks=False):
    repo = source_root(cwd)
    caller = os.path.realpath(caller or os.getcwd())
    data = worktrees.listing(repo)
    paths = [os.path.realpath(item["worktree"]["path"]) for item in data["items"] if item.get("worktree")]
    directory = Path(common_dir(repo)) / "goerwin-tools" / "removals"
    try:
        item = worktrees.resolve_existing(cwd, target, data)
    except CommandError:
        # A durable receipt makes retry possible after deletion removed the Git registration.
        candidate = Path(target).expanduser()
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        matches = [path for path in directory.glob("*.json") if (
            (record := json_read(path)).get("cleanup_pending")
            and (record.get("branch") == target or record.get("path") == str(candidate.resolve()))
        )]
        if len(matches) != 1:
            raise
        receipt = matches[0]
        result = json_read(receipt)
        with allocation_lock(directory, receipt.stem):
            result = json_read(receipt)
            save = lambda: json_write(receipt, result)
            try:
                if Path(result["path"]).exists():
                    raise CommandError("Removal is incomplete and the path still exists; inspect it before retrying")
                result["worktree_removed"] = True
                cleanup(result, [*paths, result["path"]], save)
                return result
            except (CommandError, herdr.AdapterError, OSError) as error:
                raise failure(result, error, save) from error
    folder = preflight(item, repo, caller, force)
    if item.get("branch") == data.get("repo", {}).get("default_branch"):
        raise CommandError("Worktrunk protects the default branch; switch it to another branch first")
    key = hashlib.sha256(folder.encode()).hexdigest()[:24]
    receipt = directory / (key + ".json")
    with allocation_lock(directory, key):
        inventory, selected, busy = inspect(folder, paths)
        if busy and not stop_work:
            raise CommandError("Live agents/jobs require --stop: " + ", ".join(busy))
        result = {"path": folder, "branch": item.get("branch"), "status": "prepared",
                  "created_at": now(), "receipt": str(receipt), "spaces": inventory["spaces"],
                  "stop_attempted": [], "stopped_terminals": [], "process_stop_attempted": [],
                  "stopped_processes": [], "closed_spaces": [], "space_close_attempted": [],
                  "terminal_locations": {address: {"pid": record["pid"],
                      "started": selected[record["pid"]]["started"], "folder": folder}
                      for address, record in inventory["terminals"].items()}, "worktree_removed": False,
                  "cleanup_pending": True}
        save = lambda: json_write(receipt, result)
        save()
        try:
            if busy:
                stop(folder, paths, inventory, selected, result, save)
            _, _, busy = inspect(folder, paths)
            if busy:
                raise CommandError("Shutdown could not be verified: " + ", ".join(busy))
            result["status"] = "removing"
            save()
            command = ["wt", "-C", repo, "remove", folder, "--no-delete-branch", "--foreground", "--format=json"]
            if force:
                command.append("--force")
            if no_hooks:
                command.append("--no-hooks")
            result["worktree_removed"] = None  # Dispatch/timeout may leave an uncertain outcome.
            save()
            run(command, timeout=1800, stderr=None)
            # Verify registration AND disk; a successful dispatch alone isn't completion.
            remaining = worktrees.listing(repo)
            if Path(folder).exists() or any(os.path.realpath(row["worktree"]["path"]) == folder
                    for row in remaining["items"] if row.get("worktree")):
                raise CommandError("Worktrunk returned before the checkout was removed")
            result.update(worktree_removed=True, status="cleanup")
            save()
            cleanup(result, paths, save)
            return result
        except (CommandError, herdr.AdapterError, OSError) as error:
            if result["worktree_removed"] is None:
                try:
                    remaining = worktrees.listing(repo)
                    registered = any(os.path.realpath(row["worktree"]["path"]) == folder
                                     for row in remaining["items"] if row.get("worktree"))
                    if registered == Path(folder).exists():
                        result["worktree_removed"] = not registered
                except CommandError:
                    pass
            raise failure(result, error, save) from error
