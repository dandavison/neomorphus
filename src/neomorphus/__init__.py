import click

from neomorphus import git
from neomorphus import run as run_mod
from neomorphus.actions import Action, task_context
from neomorphus.status import infer_stage, stage_artifacts
from neomorphus.workflow import DEFAULT_WORKFLOW, diagram_d2, diagram_mermaid, next_actions


def _current_actions() -> list[Action]:
    try:
        root = git.repo_root()
        stage = infer_stage(root)
        return next_actions(DEFAULT_WORKFLOW, stage)
    except Exception:
        return []


def _make_action_command(
    action: Action, interactive_action: Action | None = None
) -> click.Command:
    @click.command(name=action.name)
    @click.option("--prompt", "-p", default=None, help="Additional steering prompt")
    @click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
    @click.option("--dry-run", "-n", is_flag=True, help="Print the rendered prompt and exit")
    def handler(prompt: str | None, interactive: bool, dry_run: bool, **kwargs: str) -> None:
        chosen = interactive_action if interactive and interactive_action else action
        if chosen.human:
            click.echo(f"{chosen.name} is a human action: {chosen.prompt_template}")
            raise SystemExit(1)
        root = git.repo_root()
        stage = infer_stage(root)
        available = next_actions(DEFAULT_WORKFLOW, stage)
        if chosen not in available:
            names = list(dict.fromkeys(a.name for a in available if not a.human))
            click.echo(
                f"error: '{chosen.name}' not available at stage '{stage}'. available: {names}",
                err=True,
            )
            raise SystemExit(1)
        ctx = task_context(root)
        ctx.update(kwargs)
        if prompt:
            ctx["user_prompt"] = prompt
        rendered = chosen.render_prompt(ctx)
        if prompt and "{{user_prompt}}" not in chosen.prompt_template:
            rendered = f"{rendered}\n\nAdditional direction: {prompt}"
        if dry_run:
            click.echo(rendered)
            return
        click.echo(f"action: {chosen.name}")
        click.echo(f"prompt: {rendered[:200]}{'...' if len(rendered) > 200 else ''}")
        run_mod.run(rendered, interactive=interactive)

    for arg_name in action.args:
        handler.params.insert(0, click.Argument([arg_name], type=click.Path()))

    return handler


class DoGroup(click.Group):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        commands = self.list_commands(ctx)
        if not commands:
            formatter.write("No actions available at current stage.\n")
            formatter.write("Run 'neo next' to see what to do.\n")
            return
        super().format_help(ctx, formatter)

    def list_commands(self, ctx: click.Context) -> list[str]:
        actions = _current_actions()
        return list(dict.fromkeys(a.name for a in actions if not a.human))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        normal: Action | None = None
        interactive: Action | None = None
        for entries in DEFAULT_WORKFLOW.values():
            for a, _ in entries:
                if a.name == cmd_name:
                    if a.interactive:
                        interactive = a
                    else:
                        normal = a
        if normal is None:
            return None
        return _make_action_command(normal, interactive)


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


@app.group()
def workflow() -> None:
    """Workflow inspection commands."""


@workflow.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["mermaid", "d2"]),
    default="mermaid",
    help="Diagram format",
)
def diagram(fmt: str) -> None:
    """Print the workflow state machine as a diagram."""
    if fmt == "d2":
        click.echo(diagram_d2())
    else:
        click.echo(diagram_mermaid())


@app.command(name="run")
@click.option("--prompt", "-p", required=True, help="Prompt for the coding agent")
@click.option("--dry-run", "-n", is_flag=True, help="Print the prompt without executing")
def run_command(prompt: str, dry_run: bool) -> None:
    """Invoke Claude Code with a prompt at a clean commit."""
    if dry_run:
        click.echo(prompt)
        return
    run_mod.run(prompt)


def main() -> None:
    app()
