from pathlib import Path

from neomorphus._actions import Action, load_actions, task_context
from neomorphus._status import Stage
from neomorphus.workflows.default import DEFAULT_WORKFLOW


def test_every_stage_has_actions() -> None:
    for stage in DEFAULT_WORKFLOW._stages:
        actions = DEFAULT_WORKFLOW.next_actions(stage)
        assert len(actions) >= 1, f"no actions for {stage}"


def test_action_names_unique_per_stage() -> None:
    for stage in DEFAULT_WORKFLOW._stages:
        actions = DEFAULT_WORKFLOW.next_actions(stage)
        names = [a.name for a in actions]
        assert len(names) == len(set(names)), f"duplicate actions at {stage}"


def test_next_actions_unknown_stage() -> None:
    unknown = Stage("unknown")
    assert DEFAULT_WORKFLOW.next_actions(unknown) == []


def test_render_prompt() -> None:
    action = Action(name="test", prompt_template="Task: {{task}}")
    assert action.render_prompt({"task": "fix the bug"}) == "Task: fix the bug"


def test_render_prompt_preserves_unknown_vars() -> None:
    action = Action(name="test", prompt_template="{{known}} and {{unknown}}")
    assert action.render_prompt({"known": "yes"}) == "yes and {{unknown}}"


def test_render_prompt_with_args() -> None:
    action = Action(name="evolve", args=("target",), prompt_template="Rewrite {{target}}")
    assert action.render_prompt({"target": ".task/task.md"}) == "Rewrite .task/task.md"


def test_load_actions() -> None:
    actions = load_actions()
    names = {a.name for a in actions}
    assert {"init", "plan", "select_plan", "implement", "evolve", "evolve_interactive"} == names
    assert actions.init.human is True
    assert actions.evolve.args == ("target",)
    assert actions.evolve_interactive.args == ("target",)


def test_task_context(tmp_path: Path) -> None:
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


def test_diagram_mermaid() -> None:
    out = DEFAULT_WORKFLOW.diagram_mermaid()
    assert out.startswith("stateDiagram-v2")
    assert "no-task --> task-defined: init" in out
    assert "plan-selected --> no-task: implement" in out


def test_diagram_d2() -> None:
    out = DEFAULT_WORKFLOW.diagram_d2()
    assert "no-task -> task-defined: init" in out
    assert "plan-selected -> no-task: implement" in out
