"""Integration tests exercising the full CLI pipeline with a fake claude."""

from pathlib import Path

from click.testing import CliRunner

from neomorphus import app
from neomorphus.status import Stage, infer_stage
from tests.conftest import FakeClaude


def _setup_task(root: Path, task_text: str = "fix the widget") -> None:
    task_dir = root / ".task"
    task_dir.mkdir(exist_ok=True)
    (task_dir / "task.md").write_text(task_text)


def _commit_all(root: Path, msg: str = "setup") -> None:
    import subprocess

    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=root, check=True, capture_output=True)


def test_plan_creates_plan_file(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    _commit_all(git_repo)
    assert infer_stage(git_repo) == Stage.TASK_DEFINED

    fake_claude.script(
        actions=[{"write": ".task/plans/1.md", "content": "Step 1: do the thing"}],
        stdout="I created a plan.\n",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["do", "plan"])
    assert result.exit_code == 0, result.output

    assert (git_repo / ".task" / "plans" / "1.md").exists()
    assert infer_stage(git_repo) == Stage.PLANS_PROPOSED

    call = fake_claude.call()
    assert "fix the widget" in call["prompt"]


def test_evolve_sends_target_in_prompt(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    _commit_all(git_repo)

    fake_claude.script()

    runner = CliRunner()
    result = runner.invoke(app, ["do", "evolve", ".task/task.md"])
    assert result.exit_code == 0, result.output

    call = fake_claude.call()
    assert ".task/task.md" in call["prompt"]


def test_evolve_with_steering_prompt(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    _commit_all(git_repo)

    fake_claude.script()

    runner = CliRunner()
    result = runner.invoke(app, ["do", "evolve", ".task/task.md", "-p", "focus on errors"])
    assert result.exit_code == 0, result.output

    call = fake_claude.call()
    assert "focus on errors" in call["prompt"]


def test_select_plan_transitions_to_plan_selected(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    plans_dir = git_repo / ".task" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "1.md").write_text("Plan A")
    _commit_all(git_repo)
    assert infer_stage(git_repo) == Stage.PLANS_PROPOSED

    fake_claude.script(
        actions=[{"write": ".task/plan.md", "content": "Plan A\nSelected."}],
    )

    runner = CliRunner()
    result = runner.invoke(app, ["do", "select_plan"])
    assert result.exit_code == 0, result.output
    assert infer_stage(git_repo) == Stage.PLAN_SELECTED


def test_implement_sends_plan_in_prompt(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    (git_repo / ".task" / "plan.md").write_text("The plan")
    _commit_all(git_repo)
    assert infer_stage(git_repo) == Stage.PLAN_SELECTED

    fake_claude.script()

    runner = CliRunner()
    result = runner.invoke(app, ["do", "implement"])
    assert result.exit_code == 0, result.output

    call = fake_claude.call()
    assert "The plan" in call["prompt"]


def test_action_unavailable_at_wrong_stage(git_repo: Path) -> None:
    # no-task stage: plan should not be available
    assert infer_stage(git_repo) == Stage.NO_TASK

    runner = CliRunner()
    result = runner.invoke(app, ["do", "plan"])
    assert result.exit_code != 0
    assert "not available" in result.output or "No such command" in (result.output or "")


def test_status_shows_stage(git_repo: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "no-task" in result.output

    _setup_task(git_repo)
    _commit_all(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "task-defined" in result.output


def test_next_shows_actions(git_repo: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["next"])
    assert result.exit_code == 0
    assert "init" in result.output

    _setup_task(git_repo)
    _commit_all(git_repo)
    result = runner.invoke(app, ["next"])
    assert result.exit_code == 0
    assert "evolve" in result.output
    assert "plan" in result.output
