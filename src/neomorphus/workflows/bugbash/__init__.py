from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

OPEN = Stage("open")
DESIGNED = Stage("designed")
DONE = Stage("done")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/result.md").exists():
        return DONE
    if (root / ".task/design.md").exists():
        return DESIGNED
    return OPEN


actions = load_actions(Path(__file__).parent / "actions")

workflow = Workflow(
    transitions={
        OPEN: {actions.design: DESIGNED},
        DESIGNED: {actions.execute: DONE},
        DONE: {actions.execute: DONE},
    },
    infer_stage=infer_stage,
)
