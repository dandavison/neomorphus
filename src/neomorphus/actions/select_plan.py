from textwrap import dedent

from neomorphus.actions import Action

select_plan = Action(
    name="select_plan",
    prompt_template=dedent("""
        The following plans have been proposed:

        {plans_summary}

        Evaluate each plan for correctness, completeness, and engineering quality.
        Select the best plan and copy it to .task/plan.md,
        adding a brief justification at the top.
        """),
)
