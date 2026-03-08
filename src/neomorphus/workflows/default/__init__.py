from pathlib import Path

from neomorphus._actions import load_actions
from neomorphus._status import Stage
from neomorphus._workflow import Workflow

PLAN_SELECTED = Stage("plan-selected")
PLANS_PROPOSED = Stage("plans-proposed")
TASK_DEFINED = Stage("task-defined")
NO_TASK = Stage("no-task")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/plan.md").exists():
        return PLAN_SELECTED
    if list(root.glob(".task/plans/*.md")):
        return PLANS_PROPOSED
    if (root / ".task/task.md").exists():
        return TASK_DEFINED
    return NO_TASK


actions = load_actions()

DEFAULT_WORKFLOW = Workflow(
    transitions={
        NO_TASK: {
            actions.init: TASK_DEFINED,
        },
        TASK_DEFINED: {
            actions.evolve: TASK_DEFINED,
            actions.plan: PLANS_PROPOSED,
        },
        PLANS_PROPOSED: {
            actions.evolve: PLANS_PROPOSED,
            actions.plan: PLANS_PROPOSED,
            actions.select_plan: PLAN_SELECTED,
        },
        PLAN_SELECTED: {
            actions.implement: NO_TASK,
        },
    },
    infer_stage=infer_stage,
)
