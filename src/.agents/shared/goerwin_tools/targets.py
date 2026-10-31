"""Frozen review targets: a PR, a committed comparison, or a snapshot at HEAD."""

import hashlib
from pathlib import Path

from .runtime import (
    CommandError, commit, common_dir, current_branch, find_source, git, github, pr_url,
    remote_repositories, source_root, toplevel,
)
from .worktrees import development_branch

PR_FIELDS = (
    "id,number,url,title,state,headRefOid,baseRefOid,headRefName,baseRefName,"
    "headRepository,headRepositoryOwner"
)


def pr_target(cwd, url, settings, user=None, revision="pr", instructions=""):
    parsed = pr_url(url)
    if not parsed:
        raise CommandError("Expected a GitHub pull-request URL")
    root = find_source(cwd, parsed["repo"], settings)
    pr = github(
        ["pr", "view", parsed["url"], "--json", PR_FIELDS],
        cwd=root,
        user=user,
        host=parsed["host"],
    )
    parsed = pr_url(pr["url"])
    if not parsed:
        raise CommandError("GitHub returned an invalid pull-request URL")
    head = pr["headRefOid"]
    local_head = None
    if revision == "local":
        if common_dir(cwd) != common_dir(root):
            raise CommandError("Local revision must come from the selected source repository")
        head = local_head = commit(cwd, "HEAD")
    return {
        "version": 1,
        "kind": "pr",
        "source_root": root,
        "invoking_checkout": toplevel(cwd),
        "common_dir": common_dir(root),
        "repository": parsed["repo"],
        "target_key": parsed["url"].lower(),
        "pr_url": parsed["url"],
        "pr_number": pr["number"],
        "pr_id": pr["id"],
        "title": pr["title"],
        "pr_state": pr["state"],
        "head_ref": pr["headRefName"],
        "development_branch": development_branch(cwd, "HEAD") if revision == "local" else pr["headRefName"],
        "base_ref": pr["baseRefName"],
        "head_sha": head,
        "base_sha": pr["baseRefOid"],
        "pr_head_sha": pr["headRefOid"],
        "revision": revision,
        "local_head_sha": local_head,
        "github_user": user,
        "instructions": instructions,
    }


def comparison_target(cwd, head, base, instructions=""):
    root = source_root(cwd)
    head_sha, base_sha = commit(cwd, head), commit(cwd, base)
    return {
        "version": 1,
        "kind": "comparison",
        "source_root": root,
        "invoking_checkout": toplevel(cwd),
        "common_dir": common_dir(root),
        "repository": next(iter(remote_repositories(root).values()), root),
        "target_key": f"{common_dir(root)}:{base}...{head}",
        "title": f"{head} against {base}",
        "head_ref": head,
        "development_branch": development_branch(cwd, head),
        "base_ref": base,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "instructions": instructions,
    }


def working_tree_hash(cwd):
    """Hash of uncommitted tracked and untracked changes, or None when the tree is clean."""
    if not git(cwd, "status", "--porcelain", "--untracked-files=all").stdout:
        return None
    diff = git(cwd, "diff", "--binary", "HEAD").stdout
    untracked = git(cwd, "ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0")
    digest = hashlib.sha256(diff.encode())
    for path in filter(None, sorted(untracked)):
        digest.update(path.encode() + b"\0" + (Path(toplevel(cwd)) / path).read_bytes())
    return digest.hexdigest()


def in_place(target, cwd):
    """Review the checkout as it is: local HEAD plus any uncommitted changes."""
    head = commit(cwd, "HEAD")
    warnings = []
    if target["kind"] == "pr" and head != target["pr_head_sha"]:
        ahead, behind = git(cwd, "rev-list", "--left-right", "--count", f"HEAD...{target['pr_head_sha']}",
                            check=False).stdout.split() or ("?", "?")
        warnings.append(f"Local branch differs from the PR head ({ahead} ahead, {behind} behind); "
                        f"reviewing the local branch against {target['base_ref']}.")
    uncommitted = working_tree_hash(cwd)
    if uncommitted:
        warnings.append("The worktree has uncommitted changes; they are included in the review.")
    target = {
        **target, "head_sha": head, "revision": "local", "local_head_sha": head,
        "development_branch": current_branch(cwd), "invoking_checkout": toplevel(cwd),
        "includes_uncommitted": bool(uncommitted), "uncommitted_sha256": uncommitted,
    }
    return target, warnings


def snapshot_target(cwd, scope=".", instructions=""):
    root = source_root(cwd)
    branch = current_branch(cwd)
    return {
        "version": 1,
        "kind": "snapshot",
        "source_root": root,
        "invoking_checkout": toplevel(cwd),
        "common_dir": common_dir(root),
        "repository": next(iter(remote_repositories(root).values()), root),
        "target_key": f"{common_dir(root)}:{branch or 'HEAD'}:{scope}",
        "title": f"{scope} on {branch or 'detached HEAD'}",
        "head_ref": branch or "HEAD",
        "development_branch": branch,
        "base_ref": None,
        "head_sha": commit(cwd, "HEAD"),
        "base_sha": None,
        "scope": scope,
        "instructions": instructions,
    }
