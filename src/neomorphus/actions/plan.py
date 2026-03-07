from neomorphus.actions import Action

action = Action(
    name="plan",
    prompt_template=(
        "Read the task description in .task/task.md:\n\n{task}\n\n"
        "Propose a detailed plan to accomplish this task. "
        "Write your plan to .task/plans/{{n}}.md where {{n}} is the next available number."
    ),
)
