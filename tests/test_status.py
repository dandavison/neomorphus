from pathlib import Path

from neomorphus.workflows.default import (
    NO_TASK,
    PLAN_SELECTED,
    PLANS_PROPOSED,
    TASK_DEFINED,
    infer_stage,
)


def test_no_task_dir(tmp_path: Path) -> None:
    assert infer_stage(tmp_path) == NO_TASK


def test_empty_task_dir(tmp_path: Path) -> None:
    (tmp_path / ".task").mkdir()
    assert infer_stage(tmp_path) == NO_TASK


def test_task_defined(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    task_dir.mkdir()
    (task_dir / "task.md").write_text("fix the widget")
    assert infer_stage(tmp_path) == TASK_DEFINED


def test_plans_proposed(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    plans_dir = task_dir / "plans"
    plans_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("fix the widget")
    (plans_dir / "1.md").write_text("plan A")
    (plans_dir / "2.md").write_text("plan B")
    assert infer_stage(tmp_path) == PLANS_PROPOSED


def test_plan_selected(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    plans_dir = task_dir / "plans"
    plans_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("fix the widget")
    (plans_dir / "1.md").write_text("plan A")
    (task_dir / "plan.md").write_text("plan A")
    assert infer_stage(tmp_path) == PLAN_SELECTED
