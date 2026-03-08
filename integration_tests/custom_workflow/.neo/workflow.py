from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

draft_ready = Stage("draft-ready")
no_draft = Stage("no-draft")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/draft.md").exists():
        return draft_ready
    return no_draft


workflow = Workflow(
    transitions={
        no_draft: {actions.draft: draft_ready},
        draft_ready: {actions.finalize: no_draft},
    },
    infer_stage=infer_stage,
)
