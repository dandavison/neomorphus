#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Integration test: a user with neo on PATH defines a custom workflow.

This test does NOT import neomorphus. It interacts entirely via the neo CLI
as a subprocess, simulating a user who installed neo globally and is defining
a custom workflow in their project.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_SCENARIO = Path(__file__).resolve().parent
_FAKE_CLAUDE = str(_SCENARIO.parent.parent / "tests" / "fake_claude.py")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _neo(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "neo", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=run_env,
    )


def _commit_all(cwd: Path, msg: str = "setup") -> None:
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-m", msg)


def test_custom_workflow() -> None:
    with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as state_tmp:
        root = Path(repo_tmp)
        state_dir = Path(state_tmp)

        # Copy the scenario (a user's project with .neo/) into a fresh git repo
        for item in _SCENARIO.iterdir():
            if item.name == "test.py":
                continue
            dest = root / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        _git(root, "init")
        _git(root, "config", "user.email", "test@test.com")
        _git(root, "config", "user.name", "Test")
        _commit_all(root, "init")
        extra_env = {
            "NEO_CLAUDE_CMD": _FAKE_CLAUDE,
            "FAKE_CLAUDE_STATE": str(state_dir),
        }

        # 1. neo discovers custom workflow; stage is "no-draft"
        r = _neo(root, "status")
        assert r.returncode == 0, f"status failed: {r.stderr}"
        assert "no-draft" in r.stdout, f"expected no-draft, got: {r.stdout}"

        # 2. "draft" action is available
        r = _neo(root, "next")
        assert r.returncode == 0, f"next failed: {r.stderr}"
        assert "draft" in r.stdout, f"expected draft in next output: {r.stdout}"

        # 3. Run the draft action (fake claude writes .task/draft.md)
        script = {
            "actions": [{"write": ".task/draft.md", "content": "First draft content"}],
            "stdout": "",
            "exit_code": 0,
        }
        (state_dir / "script.json").write_text(json.dumps(script))
        r = _neo(root, "do", "draft", env=extra_env)
        assert r.returncode == 0, f"do draft failed: {r.stderr}\n{r.stdout}"

        # 4. Stage transitions to "draft-ready"
        assert (root / ".task" / "draft.md").exists()
        r = _neo(root, "status")
        assert r.returncode == 0, f"status failed: {r.stderr}"
        assert "draft-ready" in r.stdout, f"expected draft-ready, got: {r.stdout}"

        # 5. "finalize" is now available, "draft" is not
        r = _neo(root, "next")
        assert r.returncode == 0, f"next failed: {r.stderr}"
        assert "neo do finalize" in r.stdout
        assert "neo do draft" not in r.stdout

        # 6. Run finalize; prompt includes draft content
        script = {"actions": [], "stdout": "", "exit_code": 0}
        (state_dir / "script.json").write_text(json.dumps(script))
        r = _neo(root, "do", "finalize", env=extra_env)
        assert r.returncode == 0, f"do finalize failed: {r.stderr}\n{r.stdout}"

        calls_dir = state_dir / "calls"
        calls = sorted(calls_dir.glob("*.json"))
        last_call = json.loads(calls[-1].read_text())
        assert "First draft content" in last_call["prompt"], (
            f"expected draft content in prompt: {last_call['prompt'][:200]}"
        )

    print("PASS: custom workflow integration test")


if __name__ == "__main__":
    test_custom_workflow()
