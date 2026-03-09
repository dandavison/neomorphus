from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

READY = Stage("alpha-ready")
DONE = Stage("alpha-done")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/alpha.md").exists():
        return DONE
    return READY


workflow = Workflow(
    transitions={READY: {actions.go_alpha: DONE}},
    infer_stage=infer_stage,
)
