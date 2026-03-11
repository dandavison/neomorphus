"""Test that Ctrl-C kills the claude subprocess.

Uses tmux to realistically reproduce terminal signal delivery: the neo process
runs inside a tmux session's interactive shell and Ctrl-C is sent via
`tmux send-keys`, exactly as a user would do it.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

FAKE_CLAUDE_SLOW = str(Path(__file__).parent / "fake_claude_slow.py")
NEO = str(Path(__file__).parent.parent / ".venv" / "bin" / "neo")

pytestmark = pytest.mark.skipif(
    subprocess.run(["which", "tmux"], capture_output=True).returncode != 0,
    reason="tmux not available",
)


def _init_repo(path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)

    git("init")
    git("config", "user.email", "test@test.com")
    git("config", "user.name", "Test")
    (path / "init").write_text("init")
    git("add", "-A")
    git("commit", "-m", "init")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _wait_for(predicate: object, timeout: float = 10, interval: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():  # type: ignore[operator]
            return True
        time.sleep(interval)
    return False


def test_ctrl_c_kills_child(tmp_path: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    """After Ctrl-C, the claude subprocess must not remain running."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    pid_file = tmp_path_factory.mktemp("signal") / "child.pid"
    session = f"neo-test-{os.getpid()}"

    # Build the command to type into the interactive shell.
    cmd = (
        f"cd {repo} && "
        f"NEO_CLAUDE_CMD={FAKE_CLAUDE_SLOW} "
        f"FAKE_CLAUDE_PID_FILE={pid_file} "
        f"{NEO} run -p test"
    )

    try:
        # Start tmux with an interactive shell (stays open after neo exits,
        # just like a real user's terminal).
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session],
            check=True,
            capture_output=True,
        )

        # Type the command and press Enter.
        subprocess.run(
            ["tmux", "send-keys", "-t", session, cmd, "Enter"],
            check=True,
            capture_output=True,
        )

        # Wait for fake_claude to start and write its PID.
        assert _wait_for(pid_file.exists, timeout=10), "fake_claude_slow never started"
        child_pid = int(pid_file.read_text().strip())
        assert _pid_alive(child_pid), "child died before we could send Ctrl-C"

        # Small delay to ensure output is flowing.
        time.sleep(0.5)

        # Send Ctrl-C via tmux (realistic terminal SIGINT).
        subprocess.run(
            ["tmux", "send-keys", "-t", session, "C-c", ""],
            check=True,
            capture_output=True,
        )

        # The parent (neo) should kill the child. Give it up to 5 seconds.
        child_died = _wait_for(lambda: not _pid_alive(child_pid), timeout=5)

        assert child_died, f"fake_claude (pid {child_pid}) is still running after Ctrl-C"
    finally:
        subprocess.run(
            ["tmux", "kill-session", "-t", session],
            capture_output=True,
        )
        # Clean up any orphaned child.
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 9)
            except (ProcessLookupError, ValueError):
                pass
