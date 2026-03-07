from neomorphus.status import Stage
from neomorphus.workflow import DEFAULT_WORKFLOW, next_actions


def test_every_stage_has_actions():
    for stage in Stage:
        actions = next_actions(DEFAULT_WORKFLOW, stage)
        assert len(actions) >= 1, f"no actions for {stage}"


def test_action_names_unique():
    all_names: list[str] = []
    for actions in DEFAULT_WORKFLOW.values():
        all_names.extend(a.name for a in actions)
    assert len(all_names) == len(set(all_names))


def test_next_actions_unknown_stage():
    empty: dict = {}
    assert next_actions(empty, Stage.NO_TASK) == []
