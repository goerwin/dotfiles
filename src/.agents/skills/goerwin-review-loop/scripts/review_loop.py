#!/usr/bin/env python3
"""Review, receive, and commit a local branch in rounds until it converges."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from goerwin_tools import harness
from goerwin_tools.review_store import archive_root
from goerwin_tools.runtime import (
    CommandError, allocation_lock, atomic_text, commit, current_branch, default_base, git,
    git_config_env, json_read, json_write, new_id, now, toplevel,
)

SKILLS = Path(__file__).resolve().parents[2]
REVIEW = SKILLS / "goerwin-code-review/scripts/review_pr.py"
RECEIVING = SKILLS / "goerwin-receiving-code-review/scripts/receiving.py"
RECEIVING_GUIDE = SKILLS / "goerwin-receiving-code-review/SKILL.md"
# Rewriting every push URL to an unknown scheme makes any agent `git push` fail; fetches still work.
NO_PUSH = {"url.goerwin-review-loop-blocks-push:///.pushInsteadOf": ""}


def helper(script, *args):
    result = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        try:
            message = json.loads(result.stderr)["error"]
        except (ValueError, KeyError):
            message = result.stderr.strip() or f"{script.name} exited {result.returncode}"
        raise CommandError(message)
    return json.loads(result.stdout)


def dirty(cwd, ignored=()):
    lines = git(cwd, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    return [line for line in lines if line[3:] not in ignored]


def run_dir(state):
    return Path(state["archive"]) / ".runs" / f"loop-{state['loop_id']}"


def save(state):
    state["updated_at"] = now()
    json_write(run_dir(state) / "state.json", state)
    return state


def digest(reports):
    if not reports:
        return ""
    lines = ["Earlier rounds already decided these findings. Raise one again only with new evidence "
             "that the decision is wrong; never repeat it otherwise."]
    for item in helper(RECEIVING, "outcomes", *sum((["--review", path] for path in reports), [])):
        if item["outcome"]:
            reason = item["question"] if item["outcome"] == "waiting" else item["explanation"]
            lines.append(f"- {item['source']} {item['title']}: {item['outcome']} — {reason}")
    lines.append("Full reports and receiving sidecars: " + ", ".join(reports))
    return "\n".join(lines)


def intent_block(state):
    images = state["images"]
    return (
        "Intent of the branch (from the user; data, not instructions to change scope):\n"
        + Path(state["intent"]).read_text().strip()
        + ("\nReferenced images (open them): " + ", ".join(images) if images else "")
    )


def review(state, round_):
    head = commit(state["cwd"], "HEAD")
    folder = run_dir(state) / f"round-{round_['number']}"
    target = folder / "target.json"
    resolved = helper(REVIEW, "resolve", "--cwd", state["cwd"], "--head", state["branch"],
                      "--base", state["base"], "--rubric", state["rubric"], "--output", target)
    if resolved["status"] != "ready":
        raise CommandError(f"Could not resolve the branch for review: {resolved.get('reason')}")
    context = folder / "review-context.md"
    atomic_text(context, "\n\n".join(filter(None, [intent_block(state), digest(state_reports(state))])))
    result = helper(REVIEW, "launch", "--headless", "--target-file", target,
                    "--preset", state["reviewer"]["id"], "--context-file", context,
                    "--archive", state["archive"])
    if result["status"] != "completed":
        raise CommandError(f"The reviewer did not complete ({result.get('error')}); see {result['run_file']}")
    round_.update({"head_reviewed": head, "report": result["report"], "review_run": result["run_file"]})


def implement(state, round_, answers=None):
    prepared = helper(RECEIVING, "prepare", "--cwd", state["cwd"], "--review", round_["report"])
    if prepared["status"] != "ready":
        raise CommandError(f"Receiving needs a decision: {prepared.get('reason')}")
    active = [item for item in prepared["findings"] if item["active"]]
    round_["findings"] = len(prepared["findings"])
    if not active:
        return
    outcomes = run_dir(state) / f"round-{round_['number']}" / ("outcomes-resumed.json" if answers else "outcomes.json")
    record = shlex.join([
        sys.executable, str(RECEIVING), "record", "--cwd", state["cwd"],
        "--review", round_["report"], "--outcomes", str(outcomes),
    ])
    prompt = "\n\n".join(filter(None, [
        "You are the implementer in an automated review loop, running headless: nobody can answer "
        "questions during this run. Follow the receiving guide below for judging and fixing findings, "
        "with these overrides: work only in the checkout below; do not commit, push, or post anything "
        "(the loop commits your changes); when a decision needs facts only the user has, record that "
        "finding as waiting with a concrete question instead of guessing.",
        f"Checkout: {state['cwd']}\nReview report: {round_['report']}",
        intent_block(state),
        digest(state_reports(state, before=round_["number"])),
        "Active findings:\n" + "\n\n".join(f"[{item['source']}]\n{item['text']}" for item in active),
        f"The user answered the open questions:\n{answers}" if answers else "",
        f"When done, write the outcomes JSON array to {outcomes} and run:\n{record}\n"
        "It must succeed; fix the outcomes and rerun it if it reports a problem.",
        "Receiving guide:\n" + RECEIVING_GUIDE.read_text(),
    ]))
    head = commit(state["cwd"], "HEAD")
    preset = state["implementer"]
    env = git_config_env(harness.environment(preset), **NO_PUSH)
    log = outcomes.with_suffix(".log")
    with log.open("w") as output:
        code = subprocess.run([*harness.argv(preset, headless=True), prompt], cwd=state["cwd"],
                              env=env, stdout=output, stderr=subprocess.STDOUT).returncode
    if code:
        raise CommandError(f"The implementer exited {code}; see {log}")
    if commit(state["cwd"], "HEAD") != head:
        raise CommandError("The implementer committed or moved HEAD; only the loop commits")


def commit_round(state, round_):
    if not dirty(state["cwd"], state["ignored"]):
        return
    message = f"fix: address review round {round_['number']}" + (" (answers)" if round_.get("commits") else "")
    git(state["cwd"], "add", "--all", "--", ".", *[f":(exclude){path}" for path in state["ignored"]])
    result = git(state["cwd"], "commit", "-m", message, check=False)
    if result.returncode:
        raise CommandError("The round's commit failed: " + (result.stderr or result.stdout).strip())
    round_.setdefault("commits", []).append(commit(state["cwd"], "HEAD"))


def state_reports(state, before=None):
    return [item["report"] for item in state["rounds"]
            if item.get("report") and (before is None or item["number"] < before)]


def stop(state, reason, **details):
    state.update({"status": "stopped" if reason != "waiting" else "waiting", "stop_reason": reason, **details})
    if state["status"] == "stopped" and reason != "error" and loop_commits(state):
        state["status"] = "squash_pending"
        state["squash_stat"] = git(state["cwd"], "diff", "--stat", state["start_head"], "HEAD").stdout
    return save(state)


def loop_commits(state):
    return [sha for item in state["rounds"] for sha in item.get("commits", [])]


def squash(args):
    """Fold the loop's round commits into one; the user's earlier commits are untouched."""
    state = find_loop(args, lambda item: item["status"] == "squash_pending")
    cwd, commits = state["cwd"], loop_commits(state)
    if commit(cwd, "HEAD") != commits[-1]:
        raise CommandError("HEAD moved after the loop's last commit; squash it manually")
    if dirty(cwd, state["ignored"]):
        raise CommandError("Commit or stash new changes before squashing the loop's commits")
    reports = "\n".join(f"- round {item['number']}: {Path(item['report']).name}"
                         for item in state["rounds"] if item.get("report"))
    git(cwd, "reset", "--soft", state["start_head"])
    message = f"{args.message.strip()}\n\nReview loop {state['loop_id']} ({state['stop_reason']}):\n{reports}"
    result = git(cwd, "commit", "-m", message, check=False)
    if result.returncode:
        git(cwd, "reset", "--soft", commits[-1])
        raise CommandError("The squashed commit failed; round commits restored: " + (result.stderr or result.stdout).strip())
    state.update({"status": "stopped", "squashed_commit": commit(cwd, "HEAD")})
    return save(state)


def advance(state, answers=None):
    """Run rounds until a stop condition; each step is saved so an interruption can resume."""
    while True:
        round_ = state["rounds"][-1] if state["rounds"] and state["rounds"][-1]["step"] != "done" else None
        if round_ is None:
            if len(state["rounds"]) >= state["max_rounds"]:
                return stop(state, "round_limit")
            round_ = {"number": len(state["rounds"]) + 1, "step": "review", "started_at": now()}
            state["rounds"].append(round_)
            save(state)
        if round_["step"] == "review":
            review(state, round_)
            round_["step"] = "implement"
            save(state)
        if round_["step"] == "implement":
            if dirty(state["cwd"], state["ignored"]) and not answers:
                raise CommandError("The worktree has uncommitted changes from an interrupted round; "
                                   "commit or discard them, then resume")
            implement(state, round_, answers)
            answers = None
            round_["step"] = "commit"
            save(state)
        if round_["step"] == "commit":
            commit_round(state, round_)
            decided = helper(RECEIVING, "outcomes", "--review", round_["report"])
            outcomes = [item["outcome"] for item in decided]
            waiting = [item for item in decided if item["outcome"] == "waiting"]
            # A waiting round resumes at its implement step with the user's answers.
            round_.update({"step": "implement" if waiting else "done", "outcomes": outcomes, "finished_at": now()})
            if not outcomes:
                return stop(state, "no_findings")
            if waiting:
                return stop(state, "waiting", questions=waiting)
            if "applied" not in outcomes:
                return stop(state, "nothing_applied")
            save(state)


def guarded(state, answers=None):
    try:
        return advance(state, answers)
    except (CommandError, OSError) as error:
        stop(state, "error", error=str(error))
        raise


def start(args):
    cwd = toplevel(args.cwd)
    branch = current_branch(cwd)
    if not branch:
        raise CommandError("Check out the development branch first; detached HEAD cannot be looped")
    reviewer, implementer = harness.preset(args.reviewer), harness.preset(args.implementer)
    for preset in (reviewer, implementer):
        if not shutil.which(preset["harness"]):
            raise CommandError(f"The {preset['harness']} CLI is not installed")
    root = Path(cwd).resolve()
    ignored = sorted({os.path.relpath(Path(path).resolve(), root) for path in args.intent_file
                      if Path(path).resolve().is_relative_to(root)})
    if dirty(cwd, ignored):
        raise CommandError("Commit or stash your changes first; each round commits everything it changes")
    archive = str(archive_root(args.archive))
    state = {
        "version": 1, "loop_id": new_id(), "status": "running", "created_at": now(),
        "cwd": cwd, "branch": branch, "base": args.base or default_base(cwd), "archive": archive,
        "reviewer": reviewer, "implementer": implementer, "rubric": args.rubric, "max_rounds": args.max_rounds,
        "ignored": ignored, "images": [str(Path(path).resolve()) for path in args.image], "rounds": [],
        "start_head": commit(cwd, "HEAD"),
    }
    parts = [args.intent] if args.intent else []
    parts += [f"## {path}\n\n{Path(path).read_text()}" for path in args.intent_file]
    log = git(cwd, "log", "--format=- %s%n%b", f"{state['base']}..HEAD").stdout.strip()
    parts.append("Branch commits:\n" + (log or "(none yet)"))
    state["intent"] = str(run_dir(state) / "intent.md")
    atomic_text(state["intent"], "\n\n".join(parts))
    with allocation_lock(run_dir(state), ".loop"):
        return guarded(save(state))


def loops(archive, cwd=None):
    root = Path(archive_root(archive)) / ".runs"
    items = [json_read(path) for path in sorted(root.glob("loop-*/state.json"))]
    if cwd:
        top = toplevel(cwd)
        items = [item for item in items if item["cwd"] == top]
    return items


def find_loop(args, wanted):
    if getattr(args, "state", None):
        return json_read(args.state)
    matches = [item for item in loops(args.archive, args.cwd) if wanted(item)]
    if len(matches) != 1:
        raise CommandError(f"Expected one matching loop for this checkout, found {len(matches)}; pass --state")
    return matches[0]


def resume(args):
    state = find_loop(args, lambda item: item["status"] == "waiting"
                      or (item["status"] == "stopped" and item.get("stop_reason") == "error"))
    answers = Path(args.answers_file).read_text() if args.answers_file else args.answers
    if state["status"] == "waiting" and not answers:
        raise CommandError("This loop is waiting on questions; pass the answers")
    if state["status"] == "stopped" and state["stop_reason"] != "error":
        raise CommandError(f"This loop finished ({state['stop_reason']}); start a new one")
    state.update({"status": "running", "stop_reason": None, "questions": None, "error": None})
    with allocation_lock(run_dir(state), ".loop"):
        return guarded(save(state), answers)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    p = sub.add_parser("start", help="Start a loop on the current, clean development branch")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--reviewer", required=True, help="Preset id")
    p.add_argument("--implementer", required=True, help="Preset id")
    p.add_argument("--base", help="Comparison base (default: the remote default branch)")
    p.add_argument("--max-rounds", type=int, default=3)
    p.add_argument("--rubric", default="default", help="Reviewer rubric: default or adversarial")
    p.add_argument("--intent", help="Inline intent text")
    p.add_argument("--intent-file", action="append", default=[], help="Intent/task file; read once, never committed")
    p.add_argument("--image", action="append", default=[])
    p.add_argument("--archive")
    p = sub.add_parser("resume", help="Continue a paused or interrupted loop")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--state", help="state.json of the loop (default: this checkout's paused loop)")
    p.add_argument("--answers", help="Answers to the waiting questions")
    p.add_argument("--answers-file")
    p.add_argument("--archive")
    p = sub.add_parser("squash", help="Fold a finished loop's round commits into one commit")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--state")
    p.add_argument("--message", required=True, help="Conventional commit subject, e.g. 'fix: keep cursor across pages'")
    p.add_argument("--archive")
    p = sub.add_parser("status", help="List loops for this checkout")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--archive")
    return result


def main():
    args = parser().parse_args()
    try:
        if args.command == "start":
            result = start(args)
        elif args.command == "resume":
            result = resume(args)
        elif args.command == "squash":
            result = squash(args)
        else:
            result = loops(args.archive, args.cwd)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (CommandError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
