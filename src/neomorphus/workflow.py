from neomorphus.actions import Action
from neomorphus.actions.evolve import evolve, evolve_interactive
from neomorphus.actions.implement import implement
from neomorphus.actions.init import init
from neomorphus.actions.plan import plan
from neomorphus.actions.select_plan import select_plan
from neomorphus.status import Stage

Workflow = dict[Stage, list[Action]]

DEFAULT_WORKFLOW: Workflow = {
    Stage.NO_TASK: [init],
    Stage.TASK_DEFINED: [evolve, evolve_interactive, plan],
    Stage.PLANS_PROPOSED: [evolve, evolve_interactive, plan, select_plan],
    Stage.PLAN_SELECTED: [implement],
}


def next_actions(workflow: Workflow, stage: Stage) -> list[Action]:
    return workflow.get(stage, [])
