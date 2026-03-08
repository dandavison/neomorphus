from collections.abc import Iterator

from neomorphus.actions import Action, load_actions
from neomorphus.status import Stage

Workflow = dict[Stage, list[tuple[Action, Stage]]]

_actions = {(a.name, a.interactive): a for a in load_actions()}


def _a(name: str, *, interactive: bool = False) -> Action:
    return _actions[(name, interactive)]


DEFAULT_WORKFLOW: Workflow = {
    Stage.NO_TASK: [(_a("init"), Stage.TASK_DEFINED)],
    Stage.TASK_DEFINED: [
        (_a("evolve"), Stage.TASK_DEFINED),
        (_a("evolve", interactive=True), Stage.TASK_DEFINED),
        (_a("plan"), Stage.PLANS_PROPOSED),
    ],
    Stage.PLANS_PROPOSED: [
        (_a("evolve"), Stage.PLANS_PROPOSED),
        (_a("evolve", interactive=True), Stage.PLANS_PROPOSED),
        (_a("plan"), Stage.PLANS_PROPOSED),
        (_a("select_plan"), Stage.PLAN_SELECTED),
    ],
    Stage.PLAN_SELECTED: [(_a("implement"), Stage.NO_TASK)],
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
