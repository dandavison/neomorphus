"""Integration tests exercising the full CLI pipeline with a fake claude."""

from pathlib import Path

from click.testing import CliRunner

from neomorphus._cli import app
from neomorphus.workflows.default import (
    NO_TASK,
    PLAN_SELECTED,
    PLANS_PROPOSED,
    TASK_DEFINED,
)
from neomorphus.workflows.default import (
    workflow as DEFAULT_WORKFLOW,
)
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
    assert DEFAULT_WORKFLOW.stage(git_repo) == TASK_DEFINED

    fake_claude.script(
        actions=[{"write": ".task/plans/1.md", "content": "Step 1: do the thing"}],
        stdout="I created a plan.\n",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["do", "plan"])
    assert result.exit_code == 0, result.output

    assert (git_repo / ".task" / "plans" / "1.md").exists()
    assert DEFAULT_WORKFLOW.stage(git_repo) == PLANS_PROPOSED

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
    assert DEFAULT_WORKFLOW.stage(git_repo) == PLANS_PROPOSED

    fake_claude.script(
        actions=[{"write": ".task/plan.md", "content": "Plan A\nSelected."}],
    )

    runner = CliRunner()
    result = runner.invoke(app, ["do", "select_plan"])
    assert result.exit_code == 0, result.output
    assert DEFAULT_WORKFLOW.stage(git_repo) == PLAN_SELECTED


def test_implement_sends_plan_in_prompt(git_repo: Path, fake_claude: FakeClaude) -> None:
    _setup_task(git_repo)
    (git_repo / ".task" / "plan.md").write_text("The plan")
    _commit_all(git_repo)
    assert DEFAULT_WORKFLOW.stage(git_repo) == PLAN_SELECTED

    fake_claude.script()

    runner = CliRunner()
    result = runner.invoke(app, ["do", "implement"])
    assert result.exit_code == 0, result.output

    call = fake_claude.call()
    assert "The plan" in call["prompt"]


def test_action_unavailable_at_wrong_stage(git_repo: Path) -> None:
    assert DEFAULT_WORKFLOW.stage(git_repo) == NO_TASK

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


def test_workflow_list(git_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "bug-fix" in result.output
    assert "builtin" in result.output


def test_workflow_show(git_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "show"])
    assert result.exit_code == 0
    assert "stages:" in result.output
    assert "--[init]-->" in result.output


def test_workflow_use_sets_default(git_repo: Path) -> None:
    runner = CliRunner()
    # No default initially
    result = runner.invoke(app, ["workflow", "use"])
    assert result.exit_code == 0
    assert "no default" in result.output

    # Set a default
    result = runner.invoke(app, ["workflow", "use", "-w", "bug-fix"])
    assert result.exit_code == 0
    assert "bug-fix" in result.output

    # Show resolves to bug-fix without -w
    result = runner.invoke(app, ["workflow", "show"])
    assert result.exit_code == 0
    assert "--[repro]-->" in result.output

    # -w overrides stored default
    result = runner.invoke(app, ["workflow", "show", "-w", "pr-review"])
    assert result.exit_code == 0
    assert "--[review]-->" in result.output

    # Clear
    result = runner.invoke(app, ["workflow", "use", "--clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output

    # Back to default
    result = runner.invoke(app, ["workflow", "show"])
    assert result.exit_code == 0
    assert "--[init]-->" in result.output


def test_workflow_use_validates_name(git_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "use", "-w", "nonexistent"])
    assert result.exit_code != 0


def test_workflow_list_marks_current(git_repo: Path) -> None:
    runner = CliRunner()
    runner.invoke(app, ["workflow", "use", "-w", "bug-fix"])
    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0
    for line in result.output.splitlines():
        if "bug-fix" in line:
            assert "*" in line
        elif line.strip():
            assert "*" not in line


def test_workflow_show_with_name(git_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "show", "-w", "bug-fix"])
    assert result.exit_code == 0
    assert "open" in result.output
    assert "--[repro]-->" in result.output


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
