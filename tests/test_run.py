from pathlib import Path

import pytest

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.run import run


def test_dirty_repo_rejected(git_repo: Path) -> None:
    (git_repo / "dirty").write_text("dirty")
    with pytest.raises(SystemExit, match="1"):
        run("do something")


def test_clean_run_no_changes(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = git.head_sha()
    monkeypatch.setattr(run_mod, "invoke_claude", lambda prompt, **kw: 0)
    run("do nothing")
    assert git.head_sha() == before


def test_clean_run_with_changes(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = git.head_sha()

    def fake_invoke(prompt: str, **kw: object) -> int:
        (git_repo / "new_file.txt").write_text("hello")
        return 0

    monkeypatch.setattr(run_mod, "invoke_claude", fake_invoke)
    run("create a file")
    after = git.head_sha()
    assert after != before
    assert git.is_clean()
