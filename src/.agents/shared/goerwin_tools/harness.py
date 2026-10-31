"""Curated model presets and how to start each harness, interactively or headless."""

import json
import os
from pathlib import Path

from .runtime import CommandError, json_read

PRESETS = Path(__file__).resolve().parents[1] / "presets.json"


def presets(path=PRESETS):
    data = json_read(path)
    if not isinstance(data, list) or not data:
        raise CommandError("Presets must be a nonempty JSON array")
    identifiers = set()
    for preset in data:
        if not isinstance(preset, dict) or not all(preset.get(k) for k in ("id", "label", "harness", "model", "effort")):
            raise CommandError("Each preset needs id, label, harness, model, and effort")
        if preset["id"] in identifiers or preset["harness"] not in ("codex", "claude"):
            raise CommandError("Preset IDs must be unique; supported harnesses are codex and claude")
        identifiers.add(preset["id"])
    return data


def preset(identifier, path=PRESETS):
    match = next((item for item in presets(path) if item["id"] == identifier), None)
    if not match:
        raise CommandError(f"Unknown preset {identifier}; choose one from the presets list")
    return match


def argv(preset, headless=False):
    """The command before the prompt; headless runs exit when done and never ask for approval."""
    effort = "model_reasoning_effort=" + json.dumps(preset["effort"])
    if preset["harness"] == "codex":
        if headless:
            return [
                "codex", "exec", "--model", preset["model"], "-c", effort,
                "-c", 'approval_policy="never"', "--sandbox", "danger-full-access",
            ]
        return ["codex", "--no-daemon", "--model", preset["model"], "-c", effort]
    command = ["claude", "--model", preset["model"], "--effort", preset["effort"]]
    return [*command, "-p", "--permission-mode", "auto"] if headless else command


def environment(preset, env=None):
    env = dict(os.environ if env is None else env)
    if preset["harness"] == "claude":
        # This environment override outranks --effort; the explicit choice wins.
        env.pop("CLAUDE_CODE_EFFORT_LEVEL", None)
        # A fresh agent must not inherit Claude's nested-session guard.
        env.pop("CLAUDECODE", None)
    return env
