from neomorphus.actions import Action

action = Action(
    name="select_plan",
    prompt_template=(
        "The following plans have been proposed:\n\n{plans_summary}\n\n"
        "Evaluate each plan for correctness, completeness, and engineering quality. "
        "Select the best plan and copy it to .task/plan.md, "
        "adding a brief justification at the top."
    ),
)
