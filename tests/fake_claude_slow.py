#!/usr/bin/env python3
"""Fake claude that ignores SIGINT and SIGPIPE, and keeps running.

Mimics the real claude CLI's behavior: ignores terminal signals and continues
operating even when the parent process dies. The real claude (Node.js) ignores
SIGPIPE by default and handles SIGINT internally without exiting.

Env vars:
  FAKE_CLAUDE_PID_FILE  – path to write this process's PID
"""

import json
import os
import signal
import sys
import time

signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGPIPE, signal.SIG_IGN)

pid_file = os.environ.get("FAKE_CLAUDE_PID_FILE")
if pid_file:
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

for i in range(120):
    msg = {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": f"thinking... {i}"}]},
    }
    try:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()
    except BrokenPipeError:
        pass
    time.sleep(0.5)

sys.exit(0)
