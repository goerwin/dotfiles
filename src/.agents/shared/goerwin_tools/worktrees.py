import json
import os
import re
import sys
from pathlib import Path

from . import herdr_adapter
from .runtime import (
    CommandError, common_dir, config, current_branch, default_base, find_source, git,
    git_config_env, github, github_environment, pr_url, ref_exists, remote_repositories, remotes, run,
    source_root, worktrees,
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
    args = ["wt", "-C", str(repo), "switch", *(["--create"] if create else []), branch]
    if base:
        args.extend(["--base", base])
    if create:
        message = f"◎ Base for new branch {branch}: {base or 'the default branch'}"
        if sys.stderr.isatty() and os.environ.get("TERM") != "dumb" and not os.environ.get("NO_COLOR"):
            message = f"\033[36m{message}\033[0m"
        print(message, file=sys.stderr, flush=True)
    # Worktrunk writes progress and hook output to stderr; stream it so setup is visible live.
    result = run([*args, "--no-cd", "--format=json"], env=env, timeout=1800, stderr=None)
    try:
        path = str(Path(json.loads(result.stdout)["path"]).resolve())
    except (ValueError, TypeError, KeyError) as error:
        raise CommandError("Worktrunk did not return a worktree path") from error
    if common_dir(path) != common_dir(repo):
        raise CommandError("Worktrunk returned a checkout from another repository")
    if path not in {str(Path(item["worktree"]).resolve()) for item in worktrees(repo)}:
        raise CommandError("Worktrunk returned an unregistered checkout")
    return path


def remote_of(repo, ref):
    ref = ref.removeprefix("refs/remotes/")
    return next((name for name in remotes(repo) if ref.startswith(name + "/")), None)


def fetch(repo, remote, env=None):
    git(repo, "fetch", "--no-tags", "--", remote, env=env)


def development_branch(repo, ref):
    symbolic = git(repo, "rev-parse", "--symbolic-full-name", "--verify", "--end-of-options", ref, check=False).stdout.strip()
    if symbolic.startswith("refs/heads/"):
        return symbolic.removeprefix("refs/heads/")
    value = symbolic.removeprefix("refs/remotes/") if symbolic.startswith("refs/remotes/") else ref
    remote = remote_of(repo, value)
    if remote:
        return value[len(remote) + 1:]
    if symbolic.startswith("refs/tags/") or ref == "HEAD" or ref.startswith("refs/") or re.fullmatch(r"[0-9a-fA-F]{7,64}", ref):
        return None
    if git(repo, "check-ref-format", "--branch", ref, check=False).returncode == 0:
        return ref
    return None


def ensure_branch(repo, branch, base=None, env=None):
    if branch.startswith("-"):
        raise CommandError("Expected a branch name")
    git(repo, "check-ref-format", "--branch", branch)
    remote = remote_of(repo, branch)
    local = branch[len(remote) + 1:] if remote else branch
    path = branch_worktree(repo, local)
    if remote and ref_exists(repo, "refs/heads/" + local):
        tracking_remote = git(repo, "config", "--get", f"branch.{local}.remote", check=False).stdout.strip()
        merge = git(repo, "config", "--get", f"branch.{local}.merge", check=False).stdout.strip()
        if tracking_remote != remote or merge != "refs/heads/" + local:
            raise CommandError(f"Local branch {local} tracks another target; resolve the branch conflict first")
    if path:
        return {"path": path, "branch": local, "reused": True}
    if ref_exists(repo, "refs/heads/" + local):
        return {"path": switch_worktree(repo, local, env=env), "branch": local, "reused": False}
    if remote:
        fetch(repo, remote, env)
        if not ref_exists(repo, f"refs/remotes/{branch}"):
            raise CommandError(f"No remote branch {branch}")
        candidates = [remote]
    else:
        base = base or default_base(repo, env)
        base_remote = remote_of(repo, base)
        if base_remote:
            fetch(repo, base_remote, env)
        candidates = [name for name in remotes(repo) if ref_exists(repo, f"refs/remotes/{name}/{local}")]
    if not candidates:
        return {"path": switch_worktree(repo, local, create=True, base=base, env=env), "branch": local, "reused": False}
    if len(candidates) > 1 and "origin" not in candidates:
        raise CommandError(f"Multiple remotes contain {local}; use an explicit remote branch")
    chosen = "origin" if "origin" in candidates else candidates[0]
    # Git's remote-branch DWIM fails when several remotes have the branch unless told which one.
    path = switch_worktree(repo, local, env=git_config_env(env, **{"checkout.defaultRemote": chosen}))
    return {"path": path, "branch": local, "reused": False}


def pr_branch(repo, pr, parsed):
    matches = []
    head = pr["headRefName"]
    head_repo = pr.get("headRepository") or {}
    owner = pr.get("headRepositoryOwner") or {}
    head_identity = head_repo.get("nameWithOwner")
    if not head_identity and owner.get("login") and head_repo.get("name"):
        head_identity = f"{owner['login']}/{head_repo['name']}"
    identity = f"{parsed['host']}/{head_identity}".lower() if head_identity else parsed["repo"]
    known_remotes = remote_repositories(repo)
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
        remote = fields.get("remote", "")
        tracked = known_remotes.get(remote) == identity and fields.get("merge") == f"refs/heads/{head}"
        local = not remote and identity == parsed["repo"] and branch == head
        if fields.get("goerwin-pr-url", "").lower() == parsed["url"].lower() or tracked or local:
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
        known_remotes = remote_repositories(repo)
        preferred = known_remotes.get("upstream") or known_remotes.get("origin")
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
        if ref_exists(repo, "refs/heads/" + pr["headRefName"]):
            raise CommandError("A local branch with the PR's name belongs to another target; resolve the branch conflict first")
        path = switch_worktree(repo, canonical["url"], env=env)
        branch = current_branch(path)
        git(repo, "config", f"branch.{branch}.goerwin-pr-url", canonical["url"])
        result = {"path": path, "branch": branch, "reused": False}
    return {**result, "repository": canonical["repo"], "pr_url": canonical["url"]}


def focus_worktree(path, branch, focus=True):
    try:
        return herdr_adapter.focus_worktree(path, branch, focus)
    except herdr_adapter.AdapterError as error:
        return {"available": False, "warnings": [str(error)]}


def switch(target, cwd=None, base=None, config_path=None, github_user=None, focus=True, open_tab=False):
    cwd = str(Path(cwd or os.getcwd()).resolve())
    if pr_url(target) or target.isdecimal():
        if base:
            raise CommandError("A base branch is only valid when creating a named branch")
        if target.isdecimal() and int(target) < 1:
            raise CommandError("A PR number must be positive")
        result = ensure_pr(cwd, target, config(config_path) if config_path else config(), github_user)
    else:
        env = github_environment(github_user) if github_user else None
        result = ensure_branch(source_root(cwd), target, base, env)
    if focus or open_tab:
        result["herdr"] = focus_worktree(result["path"], result["branch"], focus)
    return result
