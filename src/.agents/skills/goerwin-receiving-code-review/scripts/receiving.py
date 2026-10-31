#!/usr/bin/env python3
"""Prepare local review feedback and record evidence-based receiving outcomes."""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

PRODUCER = Path(__file__).resolve().parents[2] / "goerwin-code-review" / "scripts"
sys.path.insert(0, str(PRODUCER))
import review_pr as review
import review_store as store


def sections(body):
    matches = list(re.finditer(r"^###\s+(F[1-9][0-9]*)\b[^\n]*", body, re.MULTILINE))
    if matches:
        return [
            {"id": match[1], "text": body[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(body)].strip()}
            for index, match in enumerate(matches)
        ]
    if re.search(r"\bno (?:actionable )?findings\b", body, re.IGNORECASE):
        return []
    matches = list(re.finditer(r"^(?:[0-9]+[.)]|[-*])\s+\S", body, re.MULTILINE))
    if matches:
        return [
            {"id": f"F{index + 1}", "text": body[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(body)].strip()}
            for index, match in enumerate(matches)
        ]
    return [{"id": "F1", "text": body.strip()}] if body.strip() else []


def load_paste(path, root):
    text = Path(path).read_text()
    if not text.strip():
        raise review.ReviewError("Pasted feedback is empty")
    metadata, body = store.decode(text)
    input_id = "pasted-" + hashlib.sha256(text.encode()).hexdigest()[:24]
    identifier = input_id
    try:
        parsed = store.read_report(path)
    except store.StoreError:
        parsed = None
    if parsed:
        identifier = parsed["metadata"]["review_id"]
        for original in root.glob("*.md"):
            try:
                known = store.read_report(original)
            except (OSError, store.StoreError):
                continue
            if known["metadata"]["review_id"] == identifier and (
                known["metadata"] != parsed["metadata"] or known["body"] != parsed["body"]
            ):
                raise review.ReviewError("The pasted report differs from its archived original")
    saved = root / ".inputs" / (input_id + ".md")
    if not saved.exists():
        store.atomic_text(saved, text)
    return {
        "path": str(saved), "sha256": store.digest(saved), "body": body,
        "metadata": {**metadata, "review_id": identifier},
        "pasted": True, "findings": sections(body),
    }


def prepare(args):
    root = store.archive_root(args.archive)
    cwd = str(Path(args.cwd).resolve())
    source = review.source_root(cwd)
    current_common = review.common_dir(cwd)
    identities = set(review.remote_repositories(cwd).values()) | {source}
    branch = review.git(cwd, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip()
    head = review.commit(cwd, "HEAD")
    inputs = []
    for path in args.review:
        item = store.read_report(path)
        item["findings"] = sections(item["body"])
        inputs.append(item)
    if args.text_file:
        text = Path(args.text_file).read_text()
        metadata, _ = store.decode(text)
        if not metadata.get("repository") and not args.confirm_unversioned:
            return {
                "status": "context_confirmation_required",
                "reason": "Pasted feedback has no repository/revision provenance. Confirm the intended current repository and branch.",
                "source": source, "branch": branch, "head_sha": head,
            }
        # Only persist an imported input after context confirmation.
        inputs.append(load_paste(args.text_file, root))
    if not inputs:
        raise review.ReviewError("Select one or more review files, or supply --text-file")
    wrong_repo = [
        item["path"] for item in inputs
        if item["metadata"].get("repository")
        and not (
            item["metadata"]["repository"] in identities
            or item["metadata"].get("source_common_dir") == current_common
        )
    ]
    if wrong_repo:
        return {
            "status": "repository_selection_required",
            "reason": "Selected reports belong to another repository. Choose its checkout before applying feedback.",
            "reports": wrong_repo,
        }
    targets = {item["metadata"].get("target_key") for item in inputs if item["metadata"].get("target_key")}
    if len(targets) > 1:
        return {
            "status": "target_selection_required",
            "reason": "These reports cover different targets. Select reports for one target per receiving session.",
        }
    expected = {
        item["metadata"].get("head_ref") for item in inputs if item["metadata"].get("head_ref")
    }
    if expected and branch not in expected and not args.confirm_branch:
        return {
            "status": "branch_confirmation_required",
            "reason": "The current branch differs from the reviewed branch. Ask before switching or proceeding here.",
            "current_branch": branch or None, "reviewed_branches": sorted(expected),
        }
    previous = store.receiving_outcomes(root)
    seen, findings, saved_inputs = set(), [], []
    for item in inputs:
        meta = item["metadata"]
        identifier = meta["review_id"]
        if identifier in seen:
            raise review.ReviewError("The same review was selected twice")
        seen.add(identifier)
        saved_inputs.append({
            "review_id": identifier, "path": item["path"], "sha256": item["sha256"],
            "metadata": meta,
            "stale": bool(meta.get("head_sha")) and meta["head_sha"] != head,
            "unversioned": not bool(meta.get("head_sha")),
        })
        for finding in item["findings"]:
            reference = identifier + ":" + finding["id"]
            prior = previous.get(reference)
            findings.append({
                "source": reference, "text": finding["text"],
                "active": not prior or prior["outcome"] == "waiting",
                "previous": prior,
            })
    session_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:10]
    session = {
        "version": 1, "session_id": session_id, "created_at": review.now(),
        "archive": str(root), "cwd": cwd, "source_path": source,
        "common_dir": current_common,
        "repository": inputs[0]["metadata"].get("repository") or next(iter(review.remote_repositories(cwd).values()), source),
        "branch": branch or None, "head_before": head,
        "initial_status": review.git(cwd, "status", "--porcelain").stdout,
        "inputs": saved_inputs, "findings": findings, "status": "prepared",
        "github_user": args.github_user,
    }
    session_file = root / ".receiving" / ".sessions" / (session_id + ".json")
    review.json_write(session_file, session)
    return {**session, "status": "ready", "session_file": str(session_file)}


def record(args):
    session = review.json_read(args.session_file)
    if session.get("status") != "prepared":
        raise review.ReviewError("This receiving session was already recorded")
    cwd = session["cwd"]
    if review.common_dir(cwd) != session["common_dir"]:
        raise review.ReviewError("The checkout changed repositories; prepare again")
    branch = review.git(cwd, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip() or None
    if branch != session["branch"]:
        raise review.ReviewError("The branch changed during receiving; revalidate in a new session")
    if review.commit(cwd, "HEAD") != session["head_before"]:
        raise review.ReviewError("Committed HEAD changed during receiving; revalidate in a new session")
    for item in session["inputs"]:
        if store.digest(item["path"]) != item["sha256"]:
            raise review.ReviewError("An input review changed during receiving; prepare again")
    outcomes = review.json_read(args.outcomes)
    if not isinstance(outcomes, list):
        raise review.ReviewError("Outcomes must be a JSON array")
    active = {item["source"] for item in session["findings"] if item["active"]}
    covered = set()
    for item in outcomes:
        if not isinstance(item, dict):
            raise review.ReviewError("Each outcome must be a JSON object")
        if item.get("outcome") not in ("applied", "pushed_back", "waiting"):
            raise review.ReviewError("Outcome must be applied, pushed_back, or waiting")
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources or not all(isinstance(ref, str) for ref in sources):
            raise review.ReviewError("Each outcome needs its source review/finding IDs")
        if len(sources) != len(set(sources)) or covered.intersection(sources) or not set(sources) <= active:
            raise review.ReviewError("Outcome sources must be active, selected, and addressed once")
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("explanation", "evidence")):
            raise review.ReviewError("Every decision needs an explanation and current-code evidence")
        if item["outcome"] == "waiting" and not str(item.get("question", "")).strip():
            raise review.ReviewError("Waiting outcomes need a concrete question")
        covered.update(sources)
    if covered != active:
        raise review.ReviewError("Account for every active finding; use waiting when clarification is needed")
    root = Path(session["archive"])
    local = dt.datetime.now().astimezone()
    stem = f"{local:%Y-%m-%d}_{store.slug(Path(session['source_path']).name)}_receiving_{local:%H%M%S}"
    # Serialize finalization so retries cannot create duplicate receipts.
    with review.allocation_lock(Path(args.session_file).parent, session["session_id"]):
        if review.json_read(args.session_file).get("status") != "prepared":
            raise review.ReviewError("This receiving session was already recorded")
        path = store.reserve_path(root / ".receiving", stem)
        metadata = {
            "schema_version": 1, "kind": "receiving", "receipt_id": session["session_id"],
            "created_at": review.now(), "repository": session["repository"],
            "source_path": session["source_path"], "branch": session["branch"],
            "head_before": session["head_before"], "head_after": review.commit(cwd, "HEAD"),
            "review_ids": [item["review_id"] for item in session["inputs"]],
            "github_user": session["github_user"],
            "outcomes": [{"sources": item["sources"], "outcome": item["outcome"]} for item in outcomes],
        }
        body = ["# Receiving code review", "", "## Sources", ""]
        for item in session["inputs"]:
            body.append(f"- {item['review_id']}: {item['path']}")
        body.extend(["", "## Outcomes", ""])
        if not outcomes:
            body.append("No active findings remained.")
        for index, item in enumerate(outcomes, 1):
            body.extend([
                f"### R{index}: {item['outcome']}", "",
                "Sources: " + ", ".join(item["sources"]), "",
                item["explanation"], "", "Evidence: " + item["evidence"], "",
            ])
            if item.get("question"):
                body.extend(["Question: " + item["question"], ""])
            if item.get("checks"):
                body.extend(["Checks: " + json.dumps(item["checks"], ensure_ascii=False), ""])
        store.atomic_text(path, store.encode(metadata, "\n".join(body)))
        session.update({"status": "recorded", "receipt": str(path), "recorded_at": metadata["created_at"]})
        review.json_write(args.session_file, session)
    return {"status": "recorded", "receipt": str(path), "outcomes": outcomes}


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
    p.add_argument("--archive")
    p.add_argument("--review", action="append", default=[])
    p.add_argument("--text-file")
    p.add_argument("--confirm-unversioned", action="store_true")
    p.add_argument("--confirm-branch", action="store_true")
    p.add_argument("--github-user")
    p = sub.add_parser("record", help="Save separate receiving outcomes; originals stay unchanged")
    p.add_argument("--session-file", required=True)
    p.add_argument("--outcomes", required=True)
    return result


def main():
    args = parser().parse_args()
    try:
        if args.command == "list":
            result = review.list_reviews(args)
        elif args.command == "prepare":
            result = prepare(args)
        else:
            result = record(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (review.ReviewError, store.StoreError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
