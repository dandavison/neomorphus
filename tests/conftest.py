from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)


def init_repo(path: Path) -> None:
    """Initialize a git repo with an initial commit."""
    _git(path, "init")
    _git(path, "config", "user.email", "test@test.com")
    _git(path, "config", "user.name", "Test")
    (path / "init").write_text("init")
    _git(path, "add", "-A")
    _git(path, "commit", "-m", "init")


@dataclass
class FakeClaude:
    state_dir: Path
    cmd: str
    _calls_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self._calls_dir = self.state_dir / "calls"

    def script(
        self,
        *,
        actions: list[dict[str, str]] | None = None,
        stdout: str = "",
        exit_code: int = 0,
    ) -> None:
        script = {"actions": actions or [], "stdout": stdout, "exit_code": exit_code}
        (self.state_dir / "script.json").write_text(json.dumps(script))

    def script_sequence(self, scripts: list[dict]) -> None:
        """Configure per-call scripts: scripts[i] is used for call number i."""
        for i, s in enumerate(scripts):
            (self.state_dir / f"script_{i}.json").write_text(json.dumps(s))

    def calls(self) -> list[dict]:
        files = sorted(self._calls_dir.glob("*.json"))
        return [json.loads(f.read_text()) for f in files]

    def call(self, n: int = 0) -> dict:
        return self.calls()[n]


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a git repo in tmp_path and chdir into it."""
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def fake_claude(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> FakeClaude:
    """Set up the fake claude CLI and return a FakeClaude helper."""
    state_dir = tmp_path_factory.mktemp("fake_claude")
    cmd = str(Path(__file__).parent / "fake_claude.py")
    monkeypatch.setenv("NEO_CLAUDE_CMD", cmd)
    monkeypatch.setenv("FAKE_CLAUDE_STATE", str(state_dir))
    return FakeClaude(state_dir=state_dir, cmd=cmd)
