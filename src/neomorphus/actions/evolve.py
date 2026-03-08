from textwrap import dedent

from neomorphus.actions import Action

evolve = Action(
    name="evolve",
    args=("target",),
    prompt_template=dedent("""
        Read the file {target} and research the codebase to understand the relevant code, existing
        patterns, and prior art. Then improve {target}. The objective of your improvements
        should be specified in the following (if it is not then stop and report the problem):
        """),
)

evolve_interactive = Action(
    name="evolve",
    args=("target",),
    interactive=True,
    prompt_template=dedent("""
        Read the file {target} and research the codebase to understand the relevant code, existing
        patterns, and prior art. Then work with the user to improve {target}. The objective of your
        improvements should be specified in the following (if it is not then stop and report the
        problem):
        """),
)
