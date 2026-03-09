from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

PENDING = Stage("pending")
REVIEWED = Stage("reviewed")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/review.md").exists():
        return REVIEWED
    return PENDING


workflow = Workflow(
    transitions={
        PENDING: {actions.contextualize: PENDING, actions.review: REVIEWED},
        REVIEWED: {actions.review: REVIEWED},
    },
    infer_stage=infer_stage,
)
