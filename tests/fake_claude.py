#!/usr/bin/env python3
"""Fake claude CLI for integration tests.

Reads a script from $FAKE_CLAUDE_STATE/script.json, executes scripted filesystem
actions, records the call to $FAKE_CLAUDE_STATE/calls/<N>.json, prints scripted
stdout, and exits with the scripted exit code.

Output format matches `claude --print --output-format stream-json`.
"""

import json
import os
import sys
from pathlib import Path

state_dir = Path(os.environ["FAKE_CLAUDE_STATE"])
calls_dir = state_dir / "calls"
calls_dir.mkdir(exist_ok=True)

# Parse args: extract prompt from -p <prompt> or as positional (interactive)
args = sys.argv[1:]
prompt = None
for i, arg in enumerate(args):
    if arg == "-p" and i + 1 < len(args):
        prompt = args[i + 1]
        break
if prompt is None and args and not args[0].startswith("-"):
    prompt = args[0]

# Record this call
existing = sorted(calls_dir.glob("*.json"))
n = len(existing)
call_record = {"args": args, "prompt": prompt}
(calls_dir / f"{n}.json").write_text(json.dumps(call_record))

# Read script
script_file = state_dir / "script.json"
script: dict = {}
if script_file.is_file():
    script = json.loads(script_file.read_text())

# Execute filesystem actions
for action in script.get("actions", []):
    if "write" in action:
        p = Path(action["write"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(action.get("content", ""))

# Emit stream-json output
stdout_text = script.get("stdout", "")
if stdout_text:
    msg = {
        "type": "result",
        "subtype": "success",
        "result": stdout_text,
        "session_id": "fake",
    }
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

sys.exit(script.get("exit_code", 0))
