"""The shared, dependency-free Markdown contract for both personal skills."""

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path

from .runtime import atomic_text


class StoreError(RuntimeError):
    pass


def archive_root(value=None):
    return Path(
        value or os.environ.get("GOERWIN_CODE_REVIEWS_DIR") or "~/goerwin-code-reviews"
    ).expanduser().resolve()


def slug(value, limit=48):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")[:limit] or "review"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(metadata, body):
    header = "\n".join(
        key + ": " + json.dumps(value, ensure_ascii=False)
        for key, value in metadata.items()
    )
    return "---\n" + header + "\n---\n\n" + body.strip() + "\n"


def decode(text):
    """Read the helper's flat frontmatter; every value is JSON, which is also valid YAML."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return {}, text
    end = normalized.find("\n---\n", 4)
    if end == -1:
        raise StoreError("Unterminated report frontmatter")
    metadata = {}
    for line in normalized[4:end].splitlines():
        key, separator, raw = line.partition(": ")
        if not separator or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in metadata:
            raise StoreError("Invalid or duplicate report metadata field")
        try:
            metadata[key] = json.loads(raw)
        except ValueError as error:
            raise StoreError("Report metadata must be helper-generated") from error
    return metadata, normalized[end + 5 :].lstrip("\n")


def finding_ids(body):
    ids = re.findall(r"^###\s+(F[1-9][0-9]*)\b", body, re.MULTILINE)
    if len(ids) != len(set(ids)):
        raise StoreError("Finding IDs must be unique within the report")
    if not ids and not re.search(r"\bno (?:actionable )?findings\b", body, re.IGNORECASE):
        raise StoreError("Use '### F1: ...' headings, or explicitly state 'No actionable findings.'")
    return ids


def report_path(directory, target, preset, local_time=None):
    local_time = local_time or dt.datetime.now().astimezone()
    project = slug(Path(target["source_root"]).name, 32)
    topic = (
        f"pr-{target['pr_number']}-{slug(target['title'], 42)}"
        if target["kind"] == "pr"
        else slug(target["title"], 48)
    )
    model = re.sub(
        r"[^a-z0-9.]+", "-", preset.get("filename_model", preset["model"]).lower()
    ).strip("-.")[:32]
    stem = "_".join((
        local_time.strftime("%Y-%m-%d"), project, topic,
        f"{model}-{slug(preset['effort'], 12)}", local_time.strftime("%H%M%S"),
    ))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    counter = 1
    while True:
        path = directory / f"{stem}{'' if counter == 1 else f'_{counter}'}.md"
        try:
            os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
            return path
        except FileExistsError:
            counter += 1


def report_metadata(manifest):
    target, preset = manifest["target"], manifest["preset"]
    return {
        "schema_version": 1,
        "kind": "code_review",
        "review_id": manifest["run_id"],
        "created_at": manifest["created_at"],
        "completed_at": manifest.get("finished_at"),
        "project": Path(target["source_root"]).name,
        "repository": target["repository"],
        "source_path": target["source_root"],
        "source_common_dir": target["common_dir"],
        "target_key": target["target_key"],
        "title": target["title"],
        "pr_url": target.get("pr_url"),
        "pr_number": target.get("pr_number"),
        "head_ref": target["head_ref"],
        "development_branch": target.get("development_branch"),
        "base_ref": target["base_ref"],
        "head_sha": target["head_sha"],
        "base_sha": target["base_sha"],
        "merge_base_sha": target.get("merge_base_sha"),
        "revision": target.get("revision", "local"),
        "harness": preset["harness"],
        "model": preset["model"],
        "effort": preset["effort"],
        "preset_id": preset["id"],
        "github_user": target.get("github_user"),
        "pr_changed_since_resolution": manifest.get("pr_changed_since_resolution"),
    }


def finalize_report(manifest):
    path = Path(manifest["report"])
    if not path.is_file():
        raise StoreError("Write the review report before completing the run")
    previous_digest = manifest.get("report_sha256")
    if previous_digest:
        if digest(path) != previous_digest:
            raise StoreError("The finalized original report changed; it will not be overwritten")
        return previous_digest
    _, body = decode(path.read_text())
    if not body.strip():
        raise StoreError("Write a nonempty report before completing the run")
    metadata = {**report_metadata(manifest), "finding_ids": finding_ids(body)}
    atomic_text(path, encode(metadata, body))
    return digest(path)


def read_report(path):
    path = Path(path).expanduser().resolve()
    metadata, body = decode(path.read_text())
    if metadata.get("schema_version") != 1 or metadata.get("kind") != "code_review":
        raise StoreError("Expected a saved goerwin-code-review report")
    required = ("review_id", "repository", "source_path", "head_ref", "head_sha", "base_sha")
    if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
        raise StoreError("Report provenance is incomplete")
    if metadata.get("finding_ids") != finding_ids(body):
        raise StoreError("Report finding IDs do not match its metadata")
    return {"path": str(path), "metadata": metadata, "body": body}
