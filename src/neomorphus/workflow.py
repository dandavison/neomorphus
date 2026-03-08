from collections.abc import Iterator

from neomorphus.actions import Action
from neomorphus.actions.evolve import evolve, evolve_interactive
from neomorphus.actions.implement import implement
from neomorphus.actions.init import init
from neomorphus.actions.plan import plan
from neomorphus.actions.select_plan import select_plan
from neomorphus.status import Stage

Workflow = dict[Stage, list[tuple[Action, Stage]]]

DEFAULT_WORKFLOW: Workflow = {
    Stage.NO_TASK: [(init, Stage.TASK_DEFINED)],
    Stage.TASK_DEFINED: [
        (evolve, Stage.TASK_DEFINED),
        (evolve_interactive, Stage.TASK_DEFINED),
        (plan, Stage.PLANS_PROPOSED),
    ],
    Stage.PLANS_PROPOSED: [
        (evolve, Stage.PLANS_PROPOSED),
        (evolve_interactive, Stage.PLANS_PROPOSED),
        (plan, Stage.PLANS_PROPOSED),
        (select_plan, Stage.PLAN_SELECTED),
    ],
    Stage.PLAN_SELECTED: [(implement, Stage.NO_TASK)],
}


def next_actions(workflow: Workflow, stage: Stage) -> list[Action]:
    return [action for action, _ in workflow.get(stage, [])]


def _transitions(workflow: Workflow) -> Iterator[tuple[Stage, str, Stage]]:
    seen: set[tuple[Stage, str, Stage]] = set()
    for stage, entries in workflow.items():
        for action, target in entries:
            key = (stage, action.name, target)
            if key not in seen:
                seen.add(key)
                yield key


def diagram_mermaid() -> str:
    lines = ["stateDiagram-v2"]
    for src, action, dst in _transitions(DEFAULT_WORKFLOW):
        lines.append(f"    {src.value} --> {dst.value}: {action}")
    return "\n".join(lines)


def diagram_d2() -> str:
    lines = []
    for src, action, dst in _transitions(DEFAULT_WORKFLOW):
        lines.append(f"{src.value} -> {dst.value}: {action}")
    return "\n".join(lines)
