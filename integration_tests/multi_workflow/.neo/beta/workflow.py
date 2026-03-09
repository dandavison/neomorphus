from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

READY = Stage("beta-ready")
DONE = Stage("beta-done")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/beta.md").exists():
        return DONE
    return READY


workflow = Workflow(
    transitions={READY: {actions.go_beta: DONE}},
    infer_stage=infer_stage,
)
