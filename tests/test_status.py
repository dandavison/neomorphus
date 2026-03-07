from pathlib import Path

from neomorphus.status import Stage, infer_stage, stage_artifacts


def test_no_task_dir(tmp_path: Path) -> None:
    assert infer_stage(tmp_path) == Stage.NO_TASK


def test_empty_task_dir(tmp_path: Path) -> None:
    (tmp_path / ".task").mkdir()
    assert infer_stage(tmp_path) == Stage.NO_TASK


def test_task_defined(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    task_dir.mkdir()
    (task_dir / "task.md").write_text("fix the widget")
    assert infer_stage(tmp_path) == Stage.TASK_DEFINED
    assert stage_artifacts(tmp_path, Stage.TASK_DEFINED) == [task_dir / "task.md"]


def test_plans_proposed(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    plans_dir = task_dir / "plans"
    plans_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("fix the widget")
    (plans_dir / "1.md").write_text("plan A")
    (plans_dir / "2.md").write_text("plan B")
    assert infer_stage(tmp_path) == Stage.PLANS_PROPOSED
    artifacts = stage_artifacts(tmp_path, Stage.PLANS_PROPOSED)
    assert len(artifacts) == 2
    assert all(p.suffix == ".md" for p in artifacts)


def test_plan_selected(tmp_path: Path) -> None:
    task_dir = tmp_path / ".task"
    plans_dir = task_dir / "plans"
    plans_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("fix the widget")
    (plans_dir / "1.md").write_text("plan A")
    (task_dir / "plan.md").write_text("plan A")
    assert infer_stage(tmp_path) == Stage.PLAN_SELECTED
    assert stage_artifacts(tmp_path, Stage.PLAN_SELECTED) == [task_dir / "plan.md"]
