from textwrap import dedent

from neomorphus.actions import Action

plan = Action(
    name="plan",
    prompt_template=dedent("""
        Read the task description in .task/task.md:

        {task}

        Propose a detailed plan to accomplish this task.
        Write your plan to .task/plans/{next_plan_number}.md.
        Create the .task/plans/ directory if it does not exist.
        """),
)
