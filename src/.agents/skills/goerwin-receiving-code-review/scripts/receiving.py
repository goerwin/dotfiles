#!/usr/bin/env python3
"""Select saved review feedback and record outcomes in a sidecar next to each report."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from goerwin_tools import review_store as store, worktrees
from goerwin_tools.runtime import (
    CommandError, allocation_lock, atomic_text, commit, common_dir, current_branch,
    json_read, now, pr_url, ref_exists, remote_repositories, source_root,
)

OUTCOMES = ("applied", "pushed_back", "waiting")
SIDECAR = ".receiving.md"


def sections(body):
    matches = list(re.finditer(r"^###\s+(F[1-9][0-9]*)\b[^\n]*", body, re.MULTILINE))
    numbered = not matches
    if numbered:
        if re.search(r"\bno (?:actionable )?findings\b", body, re.IGNORECASE):
            return []
        matches = list(re.finditer(r"^(?:[0-9]+[.)]|[-*])\s+\S", body, re.MULTILINE))
    if not matches:
        return [{"id": "F1", "text": body.strip()}] if body.strip() else []
    ends = [match.start() for match in matches[1:]] + [len(body)]
    return [
        {"id": f"F{index}" if numbered else match[1], "text": body[match.start():end].strip()}
        for index, (match, end) in enumerate(zip(matches, ends), 1)
    ]


def sidecar(report_path):
    path = Path(report_path)
    return path.with_name(path.stem + SIDECAR)


def outcomes_of(report):
    """Outcomes recorded for this exact report; a sidecar left by another report is ignored."""
    path = sidecar(report["path"])
    if not path.exists():
        return {}
    metadata = store.decode(path.read_text())[0]
    if metadata.get("review_id") != report["metadata"]["review_id"]:
        return {}
    return metadata.get("outcomes", {})


def list_reviews(cwd, archive=None, all_projects=False, all_branches=False, pr=None):
    root = store.archive_root(archive)
    identities, branch, head = set(), None, None
    if not all_projects:
        current = source_root(cwd)
        identities = set(remote_repositories(current).values()) | {current}
        branch, head = current_branch(cwd), commit(cwd, "HEAD")
    if pr:
        parsed = pr_url(pr)
        if not parsed:
            raise CommandError("Expected a PR URL for --pr")
        pr = parsed["url"].lower()
    rows = []
    for item in store.iter_reports(root):
        meta = item["metadata"]
        if identities and not (meta["source_path"] in identities or meta["repository"] in identities):
            continue
        if pr and (meta.get("pr_url") or "").lower() != pr:
            continue
        if not pr and identities and not all_branches and (meta.get("development_branch") or meta["head_ref"]) != branch:
            continue
        outcomes = outcomes_of(item)
        ids = meta["finding_ids"]
        rows.append({
            "review_id": meta["review_id"], "path": item["path"], "created_at": meta["created_at"],
            "project": meta["project"], "title": meta["title"], "pr_url": meta.get("pr_url"),
            "skill": meta.get("skill"), "scope": meta.get("scope"),
            "head_sha": meta["head_sha"], "model": meta["model"], "effort": meta["effort"],
            "stale": head is not None and meta["head_sha"] != head,
            "findings": len(ids),
            "remaining": sum(outcomes.get(i) not in ("applied", "pushed_back") for i in ids),
            "waiting": sum(outcomes.get(i) == "waiting" for i in ids),
        })
    rows.sort(key=lambda item: item["created_at"], reverse=True)
    return {"archive": str(root), "reviews": rows}


def development_target(cwd, inputs, selected_branch):
    expected = set()
    for meta in (item["metadata"] for item in inputs):
        branch = selected_branch or meta.get("development_branch")
        if not branch and meta["head_ref"] != "HEAD":
            branch = worktrees.development_branch(cwd, meta["head_ref"])
        if not branch:
            return None, {
                "status": "branch_selection_required", "reviewed_ref": meta["head_ref"],
                "reason": "This report does not identify a development branch. Choose one with --branch.",
            }
        expected.add(branch)
    if len(expected) > 1:
        return None, {"status": "branch_selection_required", "reviewed_branches": sorted(expected)}
    return expected.pop(), None


def navigate(cwd, branch, meta, github_user):
    path = worktrees.branch_worktree(cwd, branch)
    if path:
        return {"path": path, "branch": branch, "reused": True}
    if meta.get("pr_url") and branch == meta["head_ref"] and not ref_exists(cwd, "refs/heads/" + branch):
        return worktrees.switch(meta["pr_url"], cwd, github_user=github_user, focus=False)
    return worktrees.ensure_branch(cwd, branch, base=meta["head_sha"])


def prepare(args):
    cwd = str(Path(args.cwd).resolve())
    if args.text_file:
        body = Path(args.text_file).read_text()
        if not body.strip():
            raise CommandError("Pasted feedback is empty")
        return {
            "status": "ready", "recordable": False, "cwd": cwd, "branch": current_branch(cwd),
            "findings": [{"source": item["id"], "text": item["text"], "active": True} for item in sections(body)],
        }
    if not args.review:
        raise CommandError("Select one or more review files, or supply --text-file")
    inputs = [store.read_report(path) for path in args.review]
    if len({item["metadata"]["review_id"] for item in inputs}) != len(inputs):
        raise CommandError("The same review was selected twice")
    identities = set(remote_repositories(cwd).values()) | {source_root(cwd)}
    current_common = common_dir(cwd)
    wrong = [
        item["path"] for item in inputs
        if item["metadata"]["repository"] not in identities
        and item["metadata"].get("source_common_dir") != current_common
    ]
    if wrong:
        return {
            "status": "repository_selection_required", "reports": wrong,
            "reason": "Selected reports belong to another repository. Choose its checkout first.",
        }
    if len({item["metadata"]["target_key"] for item in inputs}) > 1:
        return {
            "status": "target_selection_required",
            "reason": "These reports cover different targets. Receive one target at a time.",
        }
    branch, blocked = development_target(cwd, inputs, args.branch)
    if blocked:
        return blocked
    navigation = None
    if branch != current_branch(cwd):
        if not args.confirm_branch:
            return {
                "status": "branch_confirmation_required", "current_branch": current_branch(cwd),
                "reviewed_branch": branch,
                "reason": "The current branch differs from the reviewed branch. Ask before switching.",
            }
        navigation = navigate(cwd, branch, inputs[0]["metadata"], args.github_user)
        cwd = navigation["path"]
        navigation["herdr"] = worktrees.focus_worktree(cwd, branch)
    head = commit(cwd, "HEAD")
    findings = []
    for item in inputs:
        meta, outcomes = item["metadata"], outcomes_of(item)
        for finding in sections(item["body"]):
            previous = outcomes.get(finding["id"])
            findings.append({
                "source": f"{meta['review_id']}:{finding['id']}", "text": finding["text"],
                "previous": previous, "active": previous in (None, "waiting"),
            })
    return {
        "status": "ready", "recordable": True, "cwd": cwd, "branch": branch, "head_sha": head,
        "reviews": [
            {"review_id": item["metadata"]["review_id"], "path": item["path"],
             "stale": item["metadata"]["head_sha"] != head, "scope": item["metadata"].get("scope")}
            for item in inputs
        ],
        "findings": findings, "worktree": navigation,
    }


def validate(outcomes, active):
    if not isinstance(outcomes, list):
        raise CommandError("Outcomes must be a JSON array")
    covered = set()
    for item in outcomes:
        if not isinstance(item, dict) or item.get("outcome") not in OUTCOMES:
            raise CommandError("Each outcome must be an object with outcome applied, pushed_back, or waiting")
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources or not all(isinstance(ref, str) for ref in sources):
            raise CommandError("Each outcome needs its source review/finding IDs")
        if len(sources) != len(set(sources)) or covered.intersection(sources) or not set(sources) <= active:
            raise CommandError("Outcome sources must be active, selected, and addressed once")
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("explanation", "evidence")):
            raise CommandError("Every decision needs an explanation and current-code evidence")
        if item["outcome"] == "waiting" and not str(item.get("question", "")).strip():
            raise CommandError("Waiting outcomes need a concrete question")
        covered.update(sources)
    if covered != active:
        raise CommandError("Account for every active finding; use waiting when clarification is needed")


def entry(item, finding_id, review_id):
    lines = [f"### {finding_id}: {item['outcome']}", ""]
    others = [ref for ref in item["sources"] if ref != f"{review_id}:{finding_id}"]
    if others:
        lines += ["Grouped with: " + ", ".join(others), ""]
    lines += [item["explanation"], "", "Evidence: " + item["evidence"], ""]
    if item.get("question"):
        lines += ["Question: " + item["question"], ""]
    if item.get("checks"):
        lines += ["Checks: " + json.dumps(item["checks"], ensure_ascii=False), ""]
    return lines


def record(args):
    inputs = {item["metadata"]["review_id"]: item for item in map(store.read_report, args.review)}
    outcomes = json_read(args.outcomes)
    active = {
        f"{review_id}:{finding_id}"
        for review_id, item in inputs.items()
        for finding_id, previous in ((i, outcomes_of(item).get(i)) for i in item["metadata"]["finding_ids"])
        if previous in (None, "waiting")
    }
    validate(outcomes, active)
    cwd = str(Path(args.cwd).resolve())
    heading = f"## {now()} · {current_branch(cwd) or 'detached'} @ {commit(cwd, 'HEAD')[:12]}"
    written = []
    for review_id, item in inputs.items():
        mine = [
            (ref.split(":", 1)[1], group) for group in outcomes for ref in group["sources"]
            if ref.split(":", 1)[0] == review_id
        ]
        if not mine:
            continue
        path = sidecar(item["path"])
        with allocation_lock(path.parent, "." + path.stem):
            existing = store.decode(path.read_text()) if path.exists() else None
            if existing and existing[0].get("review_id") != review_id:
                raise CommandError(f"{path} belongs to another report; move it aside before recording")
            metadata, body = existing or (
                {"schema_version": 1, "kind": "receiving", "review_id": review_id, "outcomes": {}},
                f"# Receiving {Path(item['path']).name}",
            )
            lines = [body.strip(), "", heading, ""]
            for finding_id, group in mine:
                metadata["outcomes"][finding_id] = group["outcome"]
                lines += entry(group, finding_id, review_id)
            atomic_text(path, store.encode(metadata, "\n".join(lines)))
        written.append(str(path))
    return {"status": "recorded", "sidecars": written}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list", help="List matching reports; never auto-select the newest")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--archive")
    p.add_argument("--all-branches", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--pr")
    p = sub.add_parser("prepare", help="Load chosen reports without changing source files")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--review", action="append", default=[])
    p.add_argument("--text-file", help="Pasted feedback; evaluated but not recorded")
    p.add_argument("--confirm-branch", action="store_true")
    p.add_argument("--branch", help="Development branch for a report of a tag, SHA, or unnamed ref")
    p.add_argument("--github-user")
    p = sub.add_parser("record", help="Append outcomes to each report's sidecar; originals stay unchanged")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--review", action="append", required=True)
    p.add_argument("--outcomes", required=True)
    return result


def main():
    args = parser().parse_args()
    try:
        if args.command == "list":
            result = list_reviews(args.cwd, args.archive, args.all, args.all_branches, args.pr)
        elif args.command == "prepare":
            result = prepare(args)
        else:
            result = record(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (CommandError, store.StoreError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
