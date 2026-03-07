from neomorphus.actions import Action

action = Action(
    name="init",
    prompt_template="Create .task/task.md describing your task, then commit.",
    human=True,
)
