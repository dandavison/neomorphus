from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

OPEN = Stage("open")
VALIDATED = Stage("validated")
PLANNED = Stage("planned")
DONE = Stage("done")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/result.md").exists():
        return DONE
    if (root / ".task/plan.md").exists():
        return PLANNED
    if (root / ".task/validation.md").exists():
        return VALIDATED
    return OPEN


actions = load_actions(Path(__file__).parent / "actions")

workflow = Workflow(
    transitions={
        OPEN: {actions.validate: VALIDATED},
        VALIDATED: {actions.plan: PLANNED},
        PLANNED: {actions.implement: DONE},
        DONE: {actions.verify: DONE},
    },
    infer_stage=infer_stage,
)
