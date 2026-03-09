from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

OPEN = Stage("open")
SPECIFIED = Stage("specified")
PLANNED = Stage("planned")
DONE = Stage("done")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/result.md").exists():
        return DONE
    if (root / ".task/plan.md").exists():
        return PLANNED
    if (root / ".task/spec.md").exists():
        return SPECIFIED
    return OPEN


actions = load_actions(Path(__file__).parent / "actions")

workflow = Workflow(
    transitions={
        OPEN: {actions.specify: SPECIFIED},
        SPECIFIED: {actions.plan: PLANNED},
        PLANNED: {actions.implement: DONE},
        DONE: {actions.verify: DONE},
    },
    infer_stage=infer_stage,
)
