from textwrap import dedent

from neomorphus.actions import Action

action = Action(
    name="evolve",
    args=("target",),
    prompt_template=dedent("""
        Read the file {target} and research the codebase to understand the relevant code, existing
        patterns, and prior art. Then improve {target}. The objective of your improvements
        should be specified in the following (if it is not then stop and report the problem):
        """),
)

interactive = Action(
    name="evolve-interactive",
    args=("target",),
    prompt_template=dedent("""
        Read the file {target} and research the codebase to understand the relevant code, existing
        patterns, and prior art. Then work with the user to improve {target}. The objective of your
        improvements should be specified in the following (if it is not then stop and report the
        problem):
        """),
    interactive=True,
)
