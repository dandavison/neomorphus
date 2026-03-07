from neomorphus.actions import Action

action = Action(
    name="implement",
    prompt_template=(
        "Implement the following plan:\n\n{plan}\n\n"
        "Follow the plan precisely. Commit your work when done."
    ),
)
