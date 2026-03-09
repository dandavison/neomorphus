from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

PLAN_SELECTED = Stage("plan-selected")
PLANS_PROPOSED = Stage("plans-proposed")
TASK_DEFINED = Stage("task-defined")
NO_TASK = Stage("no-task")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/plan.md").exists():
        return PLAN_SELECTED
    if list(root.glob(".task/plans/*.md")):
        return PLANS_PROPOSED
    if (root / ".task/task.md").exists():
        return TASK_DEFINED
    return NO_TASK


workflow = Workflow(
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
