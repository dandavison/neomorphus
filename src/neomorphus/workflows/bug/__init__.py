from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

OPEN = Stage("open")
REPRODUCED = Stage("reproduced")
PLANNED = Stage("planned")
DONE = Stage("done")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/result.md").exists():
        return DONE
    if (root / ".task/plan.md").exists():
        return PLANNED
    if (root / ".task/repro.md").exists():
        return REPRODUCED
    return OPEN


actions = load_actions(Path(__file__).parent / "actions")

workflow = Workflow(
    transitions={
        OPEN: {actions.research: REPRODUCED},
        REPRODUCED: {actions.plan: PLANNED},
        PLANNED: {actions.implement: DONE},
        DONE: {actions.verify: DONE},
    },
    infer_stage=infer_stage,
)
