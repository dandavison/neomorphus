import shutil
from pathlib import Path

import click

from neomorphus import _git as git
from neomorphus import _run as run_mod
from neomorphus._actions import Action, load_actions, task_context
from neomorphus._workflow import Workflow, load_workflow

_wf_option = click.option("-w", "--workflow", default=None, help="Workflow name or path")


def _wf_name(ctx: click.Context) -> str | None:
    c: click.Context | None = ctx
    while c is not None:
        name = c.params.get("workflow")
        if name is not None:
            return name
        c = c.parent
    return None


def _get_workflow(ctx: click.Context) -> Workflow:
    try:
        return load_workflow(git.repo_root(), _wf_name(ctx))
    except Exception:
        from neomorphus.workflows.default import DEFAULT_WORKFLOW

        return DEFAULT_WORKFLOW


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
        active_wf = load_workflow(root, _wf_name(ctx))
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
        tctx.update(kwargs)
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

    for arg_name in action.args:
        handler.params.insert(0, click.Argument([arg_name], type=click.Path()))

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
    root = git.repo_root()
    wf = load_workflow(root, _wf_name(ctx))
    stage = wf.stage(root)
    click.echo(f"stage: {stage}")


@app.command(name="next")
@_wf_option
@click.pass_context
def next_command(ctx: click.Context, workflow: str | None) -> None:  # noqa: ARG001
    """Show available actions for the current stage."""
    root = git.repo_root()
    wf = load_workflow(root, _wf_name(ctx))
    stage = wf.stage(root)
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


_INIT_WORKFLOW = """\
from pathlib import Path

from neomorphus import Stage, Workflow, load_actions

PLAN_SELECTED = Stage("plan-selected")
PLANS_PROPOSED = Stage("plans-proposed")
TASK_DEFINED = Stage("task-defined")
NO_TASK = Stage("no-task")

actions = load_actions(Path(__file__).parent / "actions")


def infer_stage(root: Path) -> Stage:
    if (root / ".task/plan.md").exists():
        return PLAN_SELECTED
    if list(root.glob(".task/plans/*.md")):
        return PLANS_PROPOSED
    if (root / ".task/task.md").exists():
        return TASK_DEFINED
    return NO_TASK


workflow = Workflow(
    transitions={
        NO_TASK: {actions.init: TASK_DEFINED},
        TASK_DEFINED: {actions.evolve: TASK_DEFINED, actions.plan: PLANS_PROPOSED},
        PLANS_PROPOSED: {
            actions.evolve: PLANS_PROPOSED,
            actions.plan: PLANS_PROPOSED,
            actions.select_plan: PLAN_SELECTED,
        },
        PLAN_SELECTED: {actions.implement: NO_TASK},
    },
    infer_stage=infer_stage,
)
"""


@app.command()
@click.argument("name", default="default")
def init(name: str) -> None:
    """Scaffold a .neo/ custom workflow."""
    root = git.repo_root()
    wf_dir = root / ".neo" / name
    if wf_dir.exists():
        click.echo(f"error: .neo/{name}/ already exists", err=True)
        raise SystemExit(1)
    actions_dir = wf_dir / "actions"
    actions_dir.mkdir(parents=True)
    (wf_dir / "workflow.py").write_text(_INIT_WORKFLOW)
    default_actions = Path(__file__).parent / "workflows" / "default"
    for md in sorted(default_actions.glob("*.md")):
        shutil.copy2(md, actions_dir / md.name)
        click.echo(f"created .neo/{name}/actions/{md.name}")
    click.echo(f"created .neo/{name}/workflow.py")
    click.echo("\nedit these files to define your workflow")


@app.group()
def workflow() -> None:
    """Workflow inspection commands."""


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
