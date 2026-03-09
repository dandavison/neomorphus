#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Integration test: a project with two workflows requires -w selection."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_SCENARIO = Path(__file__).resolve().parent


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _neo(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "neo", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=os.environ,
    )


def _commit_all(cwd: Path, msg: str = "setup") -> None:
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-m", msg)


def test_multi_workflow() -> None:
    with tempfile.TemporaryDirectory() as repo_tmp:
        root = Path(repo_tmp)

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

        # 1. Without -w, neo errors listing available workflows
        r = _neo(root, "status")
        assert r.returncode != 0, f"expected error, got: {r.stdout}"
        assert "multiple workflows" in r.stderr, f"expected multi-wf error: {r.stderr}"
        assert "alpha" in r.stderr
        assert "beta" in r.stderr

        # 2. -w alpha selects the alpha workflow
        r = _neo(root, "-w", "alpha", "status")
        assert r.returncode == 0, f"status -w alpha failed: {r.stderr}"
        assert "alpha-ready" in r.stdout, f"expected alpha-ready: {r.stdout}"

        # 3. -w beta selects the beta workflow
        r = _neo(root, "-w", "beta", "status")
        assert r.returncode == 0, f"status -w beta failed: {r.stderr}"
        assert "beta-ready" in r.stdout, f"expected beta-ready: {r.stdout}"

        # 4. -w alpha next shows alpha's action
        r = _neo(root, "-w", "alpha", "next")
        assert r.returncode == 0, f"next -w alpha failed: {r.stderr}"
        assert "go_alpha" in r.stdout, f"expected go_alpha: {r.stdout}"
        assert "go_beta" not in r.stdout

        # 5. -w beta next shows beta's action
        r = _neo(root, "-w", "beta", "next")
        assert r.returncode == 0, f"next -w beta failed: {r.stderr}"
        assert "go_beta" in r.stdout, f"expected go_beta: {r.stdout}"
        assert "go_alpha" not in r.stdout

    print("PASS: multi-workflow integration test")


if __name__ == "__main__":
    test_multi_workflow()
