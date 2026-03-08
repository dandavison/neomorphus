from neomorphus.actions import Action

evolve = Action(
    name="evolve",
    args=("target",),
    prompt_file="evolve.md",
)

evolve_interactive = Action(
    name="evolve",
    args=("target",),
    interactive=True,
    prompt_file="evolve_interactive.md",
)
