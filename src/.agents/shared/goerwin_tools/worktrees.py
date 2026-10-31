import json
import os
import re
import sys
from pathlib import Path

from . import herdr_adapter
from .runtime import (
    CommandError, common_dir, config, find_source, git, github, github_environment,
    pr_url, remote_repositories, run, source_root, worktrees,
)


def branch_worktree(repo, branch):
    entries = [item for item in worktrees(repo) if item.get("branch") == "refs/heads/" + branch]
    if len(entries) > 1:
        raise CommandError(f"Multiple worktrees contain {branch}; select a checkout explicitly")
    if not entries:
        return None
    entry = entries[0]
    if "prunable" in entry or not Path(entry["worktree"]).is_dir():
        raise CommandError(f"Worktree for {branch} is unavailable: {entry['worktree']}")
    return str(Path(entry["worktree"]).resolve())


def switch_worktree(repo, branch, create=False, base=None, env=None):
    args = ["wt", "-C", str(repo), "switch"]
    if create:
        args.append("--create")
    args.append(branch)
    if base:
        args.extend(["--base", base])
    args.extend(["--no-cd", "--format=json"])
    result = run(args, env=env, timeout=1800)
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    try:
        path = str(Path(json.loads(result.stdout)["path"]).resolve())
    except (ValueError, TypeError, KeyError) as error:
        raise CommandError("Worktrunk did not return a worktree path") from error
    if common_dir(path) != common_dir(repo):
        raise CommandError("Worktrunk returned a checkout from another repository")
    if path not in {str(Path(item["worktree"]).resolve()) for item in worktrees(repo)}:
        raise CommandError("Worktrunk returned an unregistered checkout")
    return path


def remote_ref(repo, ref):
    ref = ref.removeprefix("refs/remotes/")
    return next((name for name in git(repo, "remote").stdout.splitlines() if ref.startswith(name + "/")), None)


def development_branch(repo, ref):
    symbolic = git(repo, "rev-parse", "--symbolic-full-name", "--verify", "--end-of-options", ref, check=False).stdout.strip()
    if symbolic.startswith("refs/heads/"):
        return symbolic.removeprefix("refs/heads/")
    value = symbolic.removeprefix("refs/remotes/") if symbolic.startswith("refs/remotes/") else ref
    remote = remote_ref(repo, value)
    if remote:
        return value[len(remote) + 1:]
    if symbolic.startswith("refs/tags/") or ref == "HEAD" or re.fullmatch(r"[0-9a-fA-F]{7,64}", ref):
        return None
    if ref.startswith("refs/"):
        return None
    if git(repo, "check-ref-format", "--branch", ref, check=False).returncode == 0:
        return ref
    return None


def default_remote_base(repo, env=None):
    remotes = git(repo, "remote").stdout.splitlines()
    remote = next((name for name in ("origin", "upstream") if name in remotes), None)
    if remote is None:
        if remotes:
            if len(remotes) != 1:
                raise CommandError("Specify a base branch; the default remote is ambiguous")
            remote = remotes[0]
        else:
            raise CommandError("Specify a local base branch; this repository has no remote")
    symbolic = git(repo, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD", check=False)
    if symbolic.returncode == 0:
        return symbolic.stdout.strip().removeprefix("refs/remotes/")
    result = run(["git", "-C", str(repo), "ls-remote", "--symref", "--", remote, "HEAD"], env=env)
    match = re.search(r"^ref: refs/heads/(.+)\tHEAD$", result.stdout, re.MULTILINE)
    if not match:
        raise CommandError("Cannot determine the remote default branch; provide a base explicitly")
    return f"{remote}/{match[1]}"


def ensure_branch(repo, branch, base=None, env=None):
    if branch.startswith("-"):
        raise CommandError("Expected a branch name")
    git(repo, "check-ref-format", "--branch", branch)
    path = branch_worktree(repo, branch)
    if path:
        return {"path": path, "branch": branch, "reused": True}
    exists = git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + branch, check=False).returncode == 0
    if exists:
        return {"path": switch_worktree(repo, branch, env=env), "branch": branch, "reused": False}
    selected_remote = remote_ref(repo, branch)
    if selected_remote and git(repo, "show-ref", "--verify", "--quiet", "refs/remotes/" + branch, check=False).returncode == 0:
        local = branch[len(selected_remote) + 1:]
        if git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + local, check=False).returncode == 0:
            tracking_remote = git(repo, "config", "--get", f"branch.{local}.remote", check=False).stdout.strip()
            merge = git(repo, "config", "--get", f"branch.{local}.merge", check=False).stdout.strip()
            if tracking_remote != selected_remote or merge != "refs/heads/" + local:
                raise CommandError(f"Local branch {local} tracks another target; resolve the branch conflict first")
            return ensure_branch(repo, local, env=env)
        run(["git", "-C", str(repo), "fetch", "--no-tags", "--", selected_remote], env=env)
        return {"path": switch_worktree(repo, branch, env=env), "branch": local, "reused": False}
    remotes = git(repo, "remote").stdout.splitlines()
    candidates = [name for name in remotes if git(
        repo, "show-ref", "--verify", "--quiet", f"refs/remotes/{name}/{branch}", check=False,
    ).returncode == 0]
    if candidates:
        if len(candidates) > 1 and "origin" not in candidates:
            raise CommandError(f"Multiple remotes contain {branch}; use an explicit remote branch")
        remote = "origin" if "origin" in candidates else candidates[0]
        run(["git", "-C", str(repo), "fetch", "--no-tags", "--", remote], env=env)
        return {"path": switch_worktree(repo, f"{remote}/{branch}", env=env), "branch": branch, "reused": False}
    base = base or default_remote_base(repo, env)
    remote = remote_ref(repo, base)
    if remote:
        run(["git", "-C", str(repo), "fetch", "--no-tags", "--", remote], env=env)
    return {"path": switch_worktree(repo, branch, create=True, base=base, env=env), "branch": branch, "reused": False}


def pr_branch(repo, pr, parsed):
    matches = []
    head = pr["headRefName"]
    head_repo = pr.get("headRepository") or {}
    owner = pr.get("headRepositoryOwner") or {}
    head_identity = head_repo.get("nameWithOwner")
    if not head_identity and owner.get("login") and head_repo.get("name"):
        head_identity = f"{owner['login']}/{head_repo['name']}"
    identity = f"{parsed['host']}/{head_identity}".lower() if head_identity else parsed["repo"]
    remotes = remote_repositories(repo)
    settings = {}
    configured = git(repo, "config", "--null", "--get-regexp", r"^branch\..*\.(remote|merge|goerwin-pr-url)$", check=False)
    for item in configured.stdout.split("\0"):
        key, _, value = item.partition("\n")
        branch, _, field = key.removeprefix("branch.").rpartition(".")
        settings.setdefault(branch, {})[field] = value
    for ref in git(repo, "for-each-ref", "--format=%(refname)", "refs/heads/").stdout.splitlines():
        branch = ref.removeprefix("refs/heads/")
        if not branch or branch.startswith("chore/review-"):
            continue
        fields = settings.get(branch, {})
        association = fields.get("goerwin-pr-url", "")
        remote = fields.get("remote", "")
        merge = fields.get("merge", "")
        tracked = remotes.get(remote) == identity and merge == f"refs/heads/{head}"
        local = not remote and identity == parsed["repo"] and branch == head
        if association.lower() == parsed["url"].lower() or tracked or local:
            matches.append(branch)
    if len(matches) > 1:
        raise CommandError("Multiple development branches match this PR: " + ", ".join(matches))
    return matches[0] if matches else None


def ensure_pr(cwd, target, settings, user=None):
    parsed = pr_url(target)
    if parsed:
        repo = find_source(cwd, parsed["repo"], settings)
        host = parsed["host"]
    else:
        repo = source_root(cwd)
        remotes = remote_repositories(repo)
        preferred = remotes.get("upstream") or remotes.get("origin")
        host = preferred.split("/")[0] if preferred else None
    pr = github([
        "pr", "view", str(target), "--json",
        "url,number,headRefName,headRepository,headRepositoryOwner,isCrossRepository",
    ], repo, user, host)
    canonical = pr_url(pr.get("url", ""))
    if not canonical or (parsed and canonical["repo"] != parsed["repo"]):
        raise CommandError("GitHub returned an unexpected pull request")
    repo = find_source(repo, canonical["repo"], settings)
    existing = pr_branch(repo, pr, canonical)
    env = github_environment(user, canonical["host"])
    if existing:
        result = ensure_branch(repo, existing, env=env)
    else:
        if git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + pr["headRefName"], check=False).returncode == 0:
            raise CommandError("A local branch with the PR's name belongs to another target; resolve the branch conflict first")
        path = switch_worktree(repo, canonical["url"], env=env)
        branch = git(path, "symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip()
        git(repo, "config", f"branch.{branch}.goerwin-pr-url", canonical["url"])
        result = {"path": path, "branch": branch, "reused": False}
    return {**result, "repository": canonical["repo"], "pr_url": canonical["url"]}


def focus_worktree(path, branch):
    try:
        return herdr_adapter.focus_worktree(path, branch)
    except (herdr_adapter.AdapterError, OSError, herdr_adapter.subprocess.TimeoutExpired) as error:
        return {"available": False, "warning": str(error)}


def switch(target, cwd=None, base=None, config_path=None, github_user=None, focus=True):
    cwd = str(Path(cwd or os.getcwd()).resolve())
    if pr_url(target) or target.isdecimal():
        if base:
            raise CommandError("A base branch is only valid when creating a named branch")
        if target.isdecimal() and int(target) < 1:
            raise CommandError("A PR number must be positive")
        result = ensure_pr(cwd, target, config(config_path) if config_path else config(), github_user)
    else:
        repo = source_root(cwd)
        env = github_environment(github_user) if github_user else None
        result = ensure_branch(repo, target, base, env)
    if focus:
        result["herdr"] = focus_worktree(result["path"], result["branch"])
    return result
