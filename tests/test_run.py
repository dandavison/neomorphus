import subprocess

import pytest

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.run import run


def _git(tmp_path, *args):
    subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@test.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "init").write_text("init")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "init")


def test_dirty_repo_rejected(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "dirty").write_text("dirty")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="1"):
        run("do something")


def test_clean_run_no_changes(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = git.head_sha()
    monkeypatch.setattr(run_mod, "invoke_claude", lambda prompt: 0)
    run("do nothing")
    assert git.head_sha() == before


def test_clean_run_with_changes(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = git.head_sha()

    def fake_invoke(prompt):
        (tmp_path / "new_file.txt").write_text("hello")
        return 0

    monkeypatch.setattr(run_mod, "invoke_claude", fake_invoke)
    run("create a file")
    after = git.head_sha()
    assert after != before
    assert git.is_clean()
