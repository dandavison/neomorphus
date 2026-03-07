from neomorphus.actions import Action

action = Action(
    name="evolve",
    prompt_template=(
        "Read the task description in .task/task.md:\n\n{task}\n\n"
        "Research the codebase to understand the relevant code, existing patterns, "
        "and prior art. Then rewrite .task/task.md with a more precise, well-scoped "
        "task description. Preserve the original intent but add specificity: "
        "identify key files, clarify ambiguities, note constraints, and surface "
        "design decisions that need to be made."
    ),
)

interactive = Action(
    name="evolve-interactive",
    prompt_template=(
        "Read the task description in .task/task.md:\n\n{task}\n\n"
        "Research the codebase to understand the relevant code, existing patterns, "
        "and prior art. Then work with the user to evolve .task/task.md into a more "
        "precise, well-scoped task description."
    ),
    interactive=True,
)
