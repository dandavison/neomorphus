from pathlib import Path

from neomorphus.actions import Action, load_actions, task_context
from neomorphus.status import Stage
from neomorphus.workflow import DEFAULT_WORKFLOW, diagram_d2, diagram_mermaid, next_actions


def test_every_stage_has_actions():
    for stage in Stage:
        actions = next_actions(DEFAULT_WORKFLOW, stage)
        assert len(actions) >= 1, f"no actions for {stage}"


def test_action_names_unique_per_stage():
    for stage, entries in DEFAULT_WORKFLOW.items():
        keys = [(a.name, a.interactive) for a, _ in entries]
        assert len(keys) == len(set(keys)), f"duplicate actions at {stage}"


def test_next_actions_unknown_stage():
    empty: dict = {}
    assert next_actions(empty, Stage.NO_TASK) == []


def test_render_prompt():
    action = Action(name="test", prompt_template="Task: {{task}}")
    assert action.render_prompt({"task": "fix the bug"}) == "Task: fix the bug"


def test_render_prompt_preserves_unknown_vars():
    action = Action(name="test", prompt_template="{{known}} and {{unknown}}")
    assert action.render_prompt({"known": "yes"}) == "yes and {{unknown}}"


def test_render_prompt_with_args():
    action = Action(name="evolve", args=("target",), prompt_template="Rewrite {{target}}")
    assert action.render_prompt({"target": ".task/task.md"}) == "Rewrite .task/task.md"


def test_load_actions():
    actions = load_actions()
    names = {a.name for a in actions}
    assert {"init", "plan", "select_plan", "implement", "evolve"} == names
    by_key = {(a.name, a.interactive): a for a in actions}
    assert by_key[("init", False)].human is True
    assert by_key[("evolve", True)].interactive is True
    assert by_key[("evolve", False)].args == ("target",)


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


def test_diagram_mermaid():
    out = diagram_mermaid()
    assert out.startswith("stateDiagram-v2")
    assert "no-task --> task-defined: init" in out
    assert "plan-selected --> no-task: implement" in out


def test_diagram_d2():
    out = diagram_d2()
    assert "no-task -> task-defined: init" in out
    assert "plan-selected -> no-task: implement" in out
