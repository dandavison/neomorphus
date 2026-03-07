import sys
from typing import Annotated

import typer

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.actions import task_context
from neomorphus.status import infer_stage, stage_artifacts
from neomorphus.workflow import DEFAULT_WORKFLOW, next_actions

app = typer.Typer(add_completion=False)


@app.command()
def status() -> None:
    """Infer and display the current task stage."""
    root = git.repo_root()
    stage = infer_stage(root)
    typer.echo(f"stage: {stage}")
    for path in stage_artifacts(root, stage):
        typer.echo(f"  {path.relative_to(root)}")


@app.command(name="next")
def next_command() -> None:
    """Show available actions for the current stage."""
    root = git.repo_root()
    stage = infer_stage(root)
    actions = next_actions(DEFAULT_WORKFLOW, stage)
    if not actions:
        typer.echo(f"stage: {stage} — no actions available")
        return
    typer.echo(f"stage: {stage}")
    for action in actions:
        typer.echo(f"  {action.name}")
        typer.echo(f"    $ neo do {action.name}")


@app.command(name="do")
def do_command(
    action_name: Annotated[str, typer.Argument(help="Name of the action to execute")],
) -> None:
    """Execute a workflow action by name."""
    root = git.repo_root()
    stage = infer_stage(root)
    actions = next_actions(DEFAULT_WORKFLOW, stage)
    action = next((a for a in actions if a.name == action_name), None)
    if action is None:
        available = [a.name for a in actions]
        print(
            f"error: action '{action_name}' not available at stage '{stage}'. "
            f"available: {available}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    ctx = task_context(root)
    prompt = action.render_prompt(ctx)
    typer.echo(f"action: {action.name}")
    typer.echo(f"prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
    run_mod.run(prompt)


@app.command(name="run")
def run_command(
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt for the coding agent")],
) -> None:
    """Invoke Claude Code with a prompt at a clean commit."""
    run_mod.run(prompt)


def main() -> None:
    app()
