"""Local process inspection and identity-checked shutdown for worktree removal."""

import os
import signal
import time
from pathlib import Path

from .runtime import CommandError, run

SHELLS = {"sh", "bash", "zsh", "fish", "dash", "ksh", "nu"}


def inside(path, folder):
    return bool(path) and Path(path).resolve().is_relative_to(Path(folder).resolve())


def descendants(table, roots):
    found = set(roots)
    while True:
        added = {pid for pid, item in table.items() if item["parent"] in found} - found
        if not added:
            return found
        found.update(added)


def ancestors(table, pid=None):
    found = set()
    pid = pid or os.getpid()
    while pid and pid not in found:
        found.add(pid)
        pid = table.get(pid, {}).get("parent", 0)
    return found


def snapshot():
    """Inspect our user's processes; cwd probes use NUL fields to preserve paths."""
    listing = run(["ps", "-axo", "pid=,ppid=,uid=,stat=,lstart=,comm="])
    table = {}
    for line in listing.stdout.splitlines():
        fields = line.split(None, 9)
        if len(fields) != 10 or not all(value.isdecimal() for value in fields[:3]):
            raise CommandError("Cannot parse process listing; refusing removal")
        pid, parent, uid = map(int, fields[:3])
        table[pid] = {"pid": pid, "parent": parent, "uid": uid, "state": fields[3][0],
                      "started": " ".join(fields[4:9]), "name": fields[9], "cwd": None}
    if os.getpid() not in table:
        raise CommandError("Process inspection is incomplete; refusing removal")
    result = run(["lsof", "-nP", "-a", "-u", str(os.getuid()), "-d", "cwd", "-F0pn"], check=False)
    if result.returncode != 0 or result.stderr.strip():
        raise CommandError("Cannot inspect process working directories: " + result.stderr.strip())
    pid = None
    for field in result.stdout.split("\0"):
        field = field.removeprefix("\n")
        if field.startswith("p") and field[1:].isdecimal():
            pid = int(field[1:])
        elif field.startswith("n") and pid in table:
            table[pid]["cwd"] = field[1:]
    return table


def alive(item):
    return item["state"] not in ("Z", "X")


def associated(table, folder, roots=(), worktree_paths=()):
    def belongs(path):
        if not inside(path, folder):
            return False
        matches = [str(Path(p).resolve()) for p in worktree_paths if inside(path, p)]
        return not matches or max(matches, key=len) == str(Path(folder).resolve())

    seeds = set(roots) | {pid for pid, item in table.items() if belongs(item.get("cwd"))}
    # Inspection subprocesses belong to this command, never to the target workload.
    excluded = descendants(table, {os.getpid()})
    selected = descendants(table, seeds) - excluded
    protected = ancestors(table)
    if selected & protected:
        raise CommandError("The invoking shell/agent belongs to this worktree; remove it from another session")
    return {pid: table[pid] for pid in selected if pid in table and alive(table[pid])}


def idle_shell(item, table):
    return (Path(item["name"]).name in SHELLS and item["state"] in ("S", "I")
            and not any(alive(table[pid]) for pid in descendants(table, {item["pid"]}) - {item["pid"]}))


def signal_process(item, sig):
    """Do not signal a PID that has since been recycled or become our ancestor."""
    table = snapshot()
    current = table.get(item["pid"])
    if not current or not alive(current):
        return
    if current["started"] != item["started"]:
        raise CommandError(f"PID {item['pid']} changed identity; refusing shutdown")
    if item["pid"] in ancestors(table):
        raise CommandError("Refusing to signal the calling session")
    try:
        os.kill(item["pid"], sig)
    except ProcessLookupError:
        pass


def terminate(items, timeout=5):
    """Terminate only the inspected processes, then verify their identities exited."""
    for item in items:
        signal_process(item, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    remaining = list(items)
    while remaining and time.monotonic() < deadline:
        table = snapshot()
        remaining = [item for item in remaining if item["pid"] in table
                     and alive(table[item["pid"]]) and table[item["pid"]]["started"] == item["started"]]
        if remaining:
            time.sleep(0.1)
    for item in remaining:
        signal_process(item, signal.SIGKILL)
    if remaining:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            table = snapshot()
            remaining = [item for item in remaining if item["pid"] in table
                         and alive(table[item["pid"]]) and table[item["pid"]]["started"] == item["started"]]
            if not remaining:
                break
            time.sleep(0.1)
    if remaining:
        raise CommandError("Processes survived shutdown: " + ", ".join(str(item["pid"]) for item in remaining))
