from dataclasses import dataclass

from neomorphus.status import Stage


@dataclass(frozen=True)
class Action:
    name: str
    description: str
    command: str


Workflow = dict[Stage, list[Action]]

DEFAULT_WORKFLOW: Workflow = {
    Stage.NO_TASK: [
        Action(
            name="init",
            description="Create a task description",
            command='neo init "description of the task"',
        ),
    ],
    Stage.TASK_DEFINED: [
        Action(
            name="plan",
            description="Generate N competing plans",
            command="neo plan --count 2",
        ),
    ],
    Stage.PLANS_PROPOSED: [
        Action(
            name="select",
            description="Select a plan",
            command="neo select <n>",
        ),
    ],
    Stage.PLAN_SELECTED: [
        Action(
            name="implement",
            description="Generate an implementation from the selected plan",
            command="neo implement",
        ),
    ],
}


def next_actions(workflow: Workflow, stage: Stage) -> list[Action]:
    return workflow.get(stage, [])
