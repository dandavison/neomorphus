from neomorphus.actions import Action

action = Action(
    name="init",
    prompt_template=("Create the file .task/task.md describing the following task:\n\n{task}"),
)
