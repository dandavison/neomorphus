import shutil

import click

from neomorphus import _git as git
from neomorphus import _run as run_mod
from neomorphus._actions import Action, load_actions, task_context
from neomorphus._workflow import (
    BUILTIN_WORKFLOWS,
    Workflow,
    builtin_dir,
    clear_stored_workflow,
    list_workflows,
    load_workflow,
    store_workflow,
    stored_workflow,
)

_wf_option = click.option("-w", "--workflow", default=None, help="Workflow name or path")


def _wf_name(ctx: click.Context) -> str | None:
    c: click.Context | None = ctx
    while c is not None:
        name = c.params.get("workflow")
        if name is not None:
            return name
        c = c.parent
    return None


def _resolve_name(ctx: click.Context) -> str | None:
    """Tier 1: -w flag, Tier 2: stored default."""
    name = _wf_name(ctx)
    if name is not None:
        return name
    return stored_workflow(git.git_dir())


def _get_workflow(ctx: click.Context) -> Workflow:
    return load_workflow(git.repo_root(), _resolve_name(ctx))


def _make_action_command(action: Action) -> click.Command:
    interactive_action = _find_interactive(action.name)

    @click.command(name=action.name)
    @click.option("--prompt", "-p", default=None, help="Additional steering prompt")
    @click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
    @click.option("--dry-run", "-n", is_flag=True, help="Print the rendered prompt and exit")
    @click.pass_context
    def handler(
        ctx: click.Context,
        prompt: str | None,
        interactive: bool,
        dry_run: bool,
        **kwargs: str,
    ) -> None:
        chosen = interactive_action if interactive and interactive_action else action
        if chosen.human:
            click.echo(f"{chosen.name} is a human action: {chosen.prompt_template}")
            raise SystemExit(1)
        root = git.repo_root()
        active_wf = _get_workflow(ctx)
        stage = active_wf.stage(root)
        available = active_wf.next_actions(stage)
        if action not in available:
            names = list(dict.fromkeys(a.name for a in available if not a.human))
            click.echo(
                f"error: '{action.name}' not available at stage '{stage}'. available: {names}",
                err=True,
            )
            raise SystemExit(1)
        tctx = task_context(root)
        tctx.update({k: v for k, v in kwargs.items() if v is not None})
        if prompt:
            tctx["user_prompt"] = prompt
        rendered = chosen.render_prompt(tctx)
        if prompt and "{{user_prompt}}" not in chosen.prompt_template:
            rendered = f"{rendered}\n\nAdditional direction: {prompt}"
        if dry_run:
            click.echo(rendered)
            return
        click.echo(f"action: {chosen.name}")
        click.echo(f"prompt: {rendered[:200]}{'...' if len(rendered) > 200 else ''}")
        run_mod.run(rendered, interactive=interactive)

    for i, arg_name in enumerate(action.args):
        handler.params.insert(i, click.Argument([arg_name]))
    n = len(action.args)
    for i, arg_name in enumerate(action.optional_args):
        handler.params.insert(n + i, click.Argument([arg_name], required=False, default=None))

    return handler


def _find_interactive(name: str) -> Action | None:
    actions = load_actions()
    return getattr(actions, f"{name}_interactive", None)


class DoGroup(click.Group):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        commands = self.list_commands(ctx)
        if not commands:
            formatter.write("No actions available at current stage.\n")
            formatter.write("Run 'neo next' to see what to do.\n")
            return
        super().format_help(ctx, formatter)

    def list_commands(self, ctx: click.Context) -> list[str]:
        try:
            wf = _get_workflow(ctx)
            root = git.repo_root()
            stage = wf.stage(root)
            actions = wf.next_actions(stage)
        except Exception:
            return []
        return list(dict.fromkeys(a.name for a in actions if not a.human))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        wf = _get_workflow(ctx)
        action = wf.action(cmd_name)
        if action is None:
            return None
        return _make_action_command(action)


@click.group()
@click.option("-w", "--workflow", default=None, help="Workflow name or path")
def app(workflow: str | None) -> None:  # noqa: ARG001
    """Neomorphus: AI-assisted software development."""


@app.command()
@_wf_option
@click.pass_context
def status(ctx: click.Context, workflow: str | None) -> None:  # noqa: ARG001
    """Infer and display the current task stage."""
    wf = _get_workflow(ctx)
    stage = wf.stage(git.repo_root())
    click.echo(f"stage: {stage}")


@app.command(name="next")
@_wf_option
@click.pass_context
def next_command(ctx: click.Context, workflow: str | None) -> None:  # noqa: ARG001
    """Show available actions for the current stage."""
    wf = _get_workflow(ctx)
    stage = wf.stage(git.repo_root())
    actions = wf.next_actions(stage)
    if not actions:
        click.echo(f"stage: {stage} — no actions available")
        return
    click.echo(f"stage: {stage}")
    for action in actions:
        if action.human:
            click.echo(f"  {action.name} (human): {action.prompt_template}")
        else:
            click.echo(f"  {action.name}: $ neo do {action.name}")


_do_group = DoGroup("do", help="Execute a workflow action.")
_do_group.params.append(
    click.Option(["-w", "--workflow"], default=None, help="Workflow name or path")
)
app.add_command(_do_group)


@app.command()
@click.argument("name", default=None, required=False)
@click.option(
    "--from",
    "template",
    default="default",
    type=click.Choice(sorted(BUILTIN_WORKFLOWS)),
    help="Built-in workflow to seed from",
)
def init(name: str | None, template: str) -> None:
    """Scaffold a .neo/ custom workflow."""
    if name is None:
        name = template
    root = git.repo_root()
    wf_dir = root / ".neo" / name
    if wf_dir.exists():
        click.echo(f"error: .neo/{name}/ already exists", err=True)
        raise SystemExit(1)
    src_dir = builtin_dir(template)
    actions_dir = wf_dir / "actions"
    actions_dir.mkdir(parents=True)
    shutil.copy2(src_dir / "__init__.py", wf_dir / "workflow.py")
    for md in sorted((src_dir / "actions").glob("*.md")):
        shutil.copy2(md, actions_dir / md.name)
        click.echo(f"created .neo/{name}/actions/{md.name}")
    click.echo(f"created .neo/{name}/workflow.py")
    click.echo(f"\nseeded from builtin '{template}' — edit to customize")


@app.group()
def workflow() -> None:
    """Workflow inspection commands."""


@workflow.command(name="list")
def workflow_list() -> None:
    """List available workflows."""
    root = git.repo_root()
    current = stored_workflow(git.git_dir())
    for name, source in list_workflows(root):
        marker = " *" if name == current else ""
        click.echo(f"  {name}  ({source}){marker}")


@workflow.command()
@_wf_option
@click.option("--clear", is_flag=True, help="Remove the stored default")
@click.pass_context
def use(ctx: click.Context, workflow: str | None, clear: bool) -> None:  # noqa: ARG001
    """Set or clear the default workflow for this repo."""
    gd = git.git_dir()
    if clear:
        clear_stored_workflow(gd)
        click.echo("cleared stored workflow default")
        return
    name = _wf_name(ctx)
    if name is None:
        current = stored_workflow(gd)
        if current:
            click.echo(f"current default: {current}")
        else:
            click.echo("no default set")
        return
    # Validate that the name resolves.
    load_workflow(git.repo_root(), name)
    store_workflow(gd, name)
    click.echo(f"default workflow: {name}")


@workflow.command()
@_wf_option
@click.pass_context
def show(ctx: click.Context, workflow: str | None) -> None:  # noqa: ARG001
    """Show the workflow DAG definition."""
    wf = _get_workflow(ctx)
    click.echo(wf.describe())


@workflow.command()
@_wf_option
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["mermaid", "d2"]),
    default="mermaid",
    help="Diagram format",
)
@click.pass_context
def diagram(ctx: click.Context, workflow: str | None, fmt: str) -> None:  # noqa: ARG001
    """Print the workflow state machine as a diagram."""
    wf = _get_workflow(ctx)
    if fmt == "d2":
        click.echo(wf.diagram_d2())
    else:
        click.echo(wf.diagram_mermaid())


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
