from enum import StrEnum
from pathlib import Path


class Stage(StrEnum):
    NO_TASK = "no-task"
    TASK_DEFINED = "task-defined"
    PLANS_PROPOSED = "plans-proposed"
    PLAN_SELECTED = "plan-selected"


def infer_stage(root: Path) -> Stage:
    task_dir = root / ".task"
    if not task_dir.is_dir():
        return Stage.NO_TASK
    if (task_dir / "plan.md").is_file():
        return Stage.PLAN_SELECTED
    if list((task_dir / "plans").glob("*.md")) if (task_dir / "plans").is_dir() else []:
        return Stage.PLANS_PROPOSED
    if (task_dir / "task.md").is_file():
        return Stage.TASK_DEFINED
    return Stage.NO_TASK


def stage_artifacts(root: Path, stage: Stage) -> list[Path]:
    task_dir = root / ".task"
    match stage:
        case Stage.NO_TASK:
            return []
        case Stage.TASK_DEFINED:
            return [task_dir / "task.md"]
        case Stage.PLANS_PROPOSED:
            plans_dir = task_dir / "plans"
            return sorted(plans_dir.glob("*.md")) if plans_dir.is_dir() else []
        case Stage.PLAN_SELECTED:
            return [task_dir / "plan.md"]
