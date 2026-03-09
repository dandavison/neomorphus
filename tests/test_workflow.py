from pathlib import Path

import pytest

from neomorphus._actions import Action, load_actions, task_context
from neomorphus._status import Stage
from neomorphus._workflow import Workflow, load_workflow
from neomorphus.workflows.default import workflow as DEFAULT_WORKFLOW

_MINIMAL_WORKFLOW = """\
from pathlib import Path
from neomorphus import Stage, Workflow, load_actions

A = Stage("a")
B = Stage("b")
actions = load_actions(Path(__file__).parent / "actions")

def infer_stage(root: Path) -> Stage:
    return A

workflow = Workflow(
    transitions={A: {actions.go: B}},
    infer_stage=infer_stage,
)
"""

_MINIMAL_ACTION = """\
---
name: go
---
Do the thing.
"""


def _create_workflow(neo_dir: Path, name: str) -> None:
    wf_dir = neo_dir / name
    actions_dir = wf_dir / "actions"
    actions_dir.mkdir(parents=True)
    (wf_dir / "workflow.py").write_text(_MINIMAL_WORKFLOW)
    (actions_dir / "go.md").write_text(_MINIMAL_ACTION)


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


# --- load_workflow resolution tests ---


def test_no_neo_dir_returns_default(tmp_path: Path) -> None:
    wf = load_workflow(tmp_path)
    assert wf is DEFAULT_WORKFLOW


def test_single_subdir_implicit(tmp_path: Path) -> None:
    _create_workflow(tmp_path / ".neo", "issue")
    wf = load_workflow(tmp_path)
    assert isinstance(wf, Workflow)
    assert wf is not DEFAULT_WORKFLOW


def test_explicit_name(tmp_path: Path) -> None:
    neo_dir = tmp_path / ".neo"
    _create_workflow(neo_dir, "issue")
    _create_workflow(neo_dir, "pr_review")
    wf = load_workflow(tmp_path, name="issue")
    assert isinstance(wf, Workflow)


def test_multiple_subdir_no_name_errors(tmp_path: Path) -> None:
    neo_dir = tmp_path / ".neo"
    _create_workflow(neo_dir, "issue")
    _create_workflow(neo_dir, "pr_review")
    with pytest.raises(ValueError, match="multiple workflows"):
        load_workflow(tmp_path)


def test_neo_dir_exists_but_no_workflows_errors(tmp_path: Path) -> None:
    (tmp_path / ".neo").mkdir()
    with pytest.raises(ValueError, match="no workflows"):
        load_workflow(tmp_path)


def test_explicit_name_missing_errors(tmp_path: Path) -> None:
    (tmp_path / ".neo").mkdir()
    with pytest.raises(ValueError, match="not found"):
        load_workflow(tmp_path, name="nonexistent")


def test_file_path_resolution(tmp_path: Path) -> None:
    _create_workflow(tmp_path / ".neo", "issue")
    wf_file = tmp_path / ".neo" / "issue" / "workflow.py"
    wf = load_workflow(tmp_path, name=str(wf_file))
    assert isinstance(wf, Workflow)


def test_builtin_bug_fix(tmp_path: Path) -> None:
    from neomorphus.workflows.bug_fix import workflow as bug_fix_wf

    wf = load_workflow(tmp_path, name="bug-fix")
    assert wf is bug_fix_wf


def test_builtin_pr_review(tmp_path: Path) -> None:
    from neomorphus.workflows.pr_review import workflow as pr_review_wf

    wf = load_workflow(tmp_path, name="pr-review")
    assert wf is pr_review_wf


def test_builtin_unknown_errors(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown workflow"):
        load_workflow(tmp_path, name="nonexistent")


def test_list_workflows_no_neo_dir(tmp_path: Path) -> None:
    from neomorphus._workflow import list_workflows

    result = list_workflows(tmp_path)
    assert result == [("bug-fix", "builtin"), ("default", "builtin"), ("pr-review", "builtin")]


def test_list_workflows_with_neo_dir(tmp_path: Path) -> None:
    from neomorphus._workflow import list_workflows

    neo_dir = tmp_path / ".neo"
    _create_workflow(neo_dir, "alpha")
    _create_workflow(neo_dir, "beta")
    result = list_workflows(tmp_path)
    assert result == [("alpha", "custom"), ("beta", "custom")]


def test_stored_workflow_roundtrip(tmp_path: Path) -> None:
    from neomorphus._workflow import clear_stored_workflow, store_workflow, stored_workflow

    assert stored_workflow(tmp_path) is None
    store_workflow(tmp_path, "bug-fix")
    assert stored_workflow(tmp_path) == "bug-fix"
    store_workflow(tmp_path, "pr-review")
    assert stored_workflow(tmp_path) == "pr-review"
    clear_stored_workflow(tmp_path)
    assert stored_workflow(tmp_path) is None
    # clearing when already absent is fine
    clear_stored_workflow(tmp_path)


def test_describe() -> None:
    out = DEFAULT_WORKFLOW.describe()
    assert out.startswith("stages:")
    assert "no-task" in out
    assert "--[init]-->" in out


def test_neo_dir_shadows_builtins(tmp_path: Path) -> None:
    """When .neo/ exists, builtin names are NOT resolved."""
    _create_workflow(tmp_path / ".neo", "other")
    with pytest.raises(ValueError, match="not found"):
        load_workflow(tmp_path, name="bug-fix")
