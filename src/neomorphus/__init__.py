from typing import Annotated

import typer

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.status import infer_stage, stage_artifacts

app = typer.Typer(add_completion=False)


@app.command()
def status() -> None:
    """Infer and display the current task stage."""
    root = git.repo_root()
    stage = infer_stage(root)
    typer.echo(f"stage: {stage}")
    for path in stage_artifacts(root, stage):
        typer.echo(f"  {path.relative_to(root)}")


@app.command(name="run")
def run_command(
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt for the coding agent")],
) -> None:
    """Invoke Claude Code with a prompt at a clean commit."""
    run_mod.run(prompt)


def main() -> None:
    app()
