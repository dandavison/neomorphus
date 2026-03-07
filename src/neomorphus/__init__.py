import click

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.actions import Action, task_context
from neomorphus.status import infer_stage, stage_artifacts
from neomorphus.workflow import DEFAULT_WORKFLOW, next_actions


def _current_actions() -> list[Action]:
    try:
        root = git.repo_root()
        stage = infer_stage(root)
        return next_actions(DEFAULT_WORKFLOW, stage)
    except Exception:
        return []


def _make_action_command(action: Action) -> click.Command:
    @click.command(name=action.name)
    @click.option("--prompt", "-p", default=None, help="Additional steering prompt")
    def handler(prompt: str | None) -> None:
        if action.human:
            click.echo(f"{action.name} is a human action: {action.prompt_template}")
            raise SystemExit(1)
        root = git.repo_root()
        stage = infer_stage(root)
        available = next_actions(DEFAULT_WORKFLOW, stage)
        if action not in available:
            names = [a.name for a in available if not a.human]
            click.echo(
                f"error: '{action.name}' not available at stage '{stage}'. available: {names}",
                err=True,
            )
            raise SystemExit(1)
        ctx = task_context(root)
        if prompt:
            ctx["user_prompt"] = prompt
        rendered = action.render_prompt(ctx)
        if prompt and "{user_prompt}" not in action.prompt_template:
            rendered = f"{rendered}\n\nAdditional direction: {prompt}"
        click.echo(f"action: {action.name}")
        click.echo(f"prompt: {rendered[:200]}{'...' if len(rendered) > 200 else ''}")
        run_mod.run(rendered, interactive=action.interactive)

    return handler


class DoGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        actions = _current_actions()
        return [a.name for a in actions if not a.human]

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        all_actions: dict[str, Action] = {}
        for actions in DEFAULT_WORKFLOW.values():
            for a in actions:
                all_actions[a.name] = a
        action = all_actions.get(cmd_name)
        if action is None:
            return None
        return _make_action_command(action)


@click.group()
def app() -> None:
    """Neomorphus: AI-assisted software development."""


@app.command()
def status() -> None:
    """Infer and display the current task stage."""
    root = git.repo_root()
    stage = infer_stage(root)
    click.echo(f"stage: {stage}")
    for path in stage_artifacts(root, stage):
        click.echo(f"  {path.relative_to(root)}")


@app.command(name="next")
def next_command() -> None:
    """Show available actions for the current stage."""
    root = git.repo_root()
    stage = infer_stage(root)
    actions = next_actions(DEFAULT_WORKFLOW, stage)
    if not actions:
        click.echo(f"stage: {stage} — no actions available")
        return
    click.echo(f"stage: {stage}")
    for action in actions:
        if action.human:
            click.echo(f"  {action.name} (human): {action.prompt_template}")
        else:
            click.echo(f"  {action.name}: $ neo do {action.name}")


app.add_command(DoGroup("do", help="Execute a workflow action."))


@app.command(name="run")
@click.option("--prompt", "-p", required=True, help="Prompt for the coding agent")
def run_command(prompt: str) -> None:
    """Invoke Claude Code with a prompt at a clean commit."""
    run_mod.run(prompt)


def main() -> None:
    app()
