from textwrap import dedent

from neomorphus.actions import Action

implement = Action(
    name="implement",
    prompt_template=dedent("""
        Implement the following plan:

        {plan}

        Follow the plan precisely. Commit your work when done.
        """),
)
