from pathlib import Path

from neomorphus.actions import Action, task_context
from neomorphus.status import Stage
from neomorphus.workflow import DEFAULT_WORKFLOW, next_actions


def test_every_stage_has_actions():
    for stage in Stage:
        actions = next_actions(DEFAULT_WORKFLOW, stage)
        assert len(actions) >= 1, f"no actions for {stage}"


def test_action_names_unique_per_stage():
    for stage, actions in DEFAULT_WORKFLOW.items():
        names = [a.name for a in actions]
        assert len(names) == len(set(names)), f"duplicate action names at {stage}"


def test_next_actions_unknown_stage():
    empty: dict = {}
    assert next_actions(empty, Stage.NO_TASK) == []


def test_render_prompt():
    action = Action(name="test", prompt_template="Task: {task}")
    assert action.render_prompt({"task": "fix the bug"}) == "Task: fix the bug"


def test_task_context(tmp_path: Path):
    task_dir = tmp_path / ".task"
    task_dir.mkdir()
    (task_dir / "task.md").write_text("fix the widget")
    plans_dir = task_dir / "plans"
    plans_dir.mkdir()
    (plans_dir / "1.md").write_text("plan A")
    (plans_dir / "2.md").write_text("plan B")
    (task_dir / "plan.md").write_text("plan A")

    ctx = task_context(tmp_path)
    assert ctx["task"] == "fix the widget"
    assert ctx["plan"] == "plan A"
    assert ctx["plan_1"] == "plan A"
    assert ctx["plan_2"] == "plan B"
    assert "Plan 1" in ctx["plans_summary"]
    assert "Plan 2" in ctx["plans_summary"]
