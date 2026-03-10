# Implementation plan: `neo do` auto-advance

## Analysis

The core change is making `DoGroup` handle the no-subcommand case by running
the auto-advance loop instead of showing help.

### Key observations

1. **Click `Group.invoke()`** calls `result_callback` when no subcommand is given.
   `DoGroup` can override `invoke()` to detect "no subcommand" and run auto-advance.

2. **`run()` in `_run.py` enforces clean-tree precondition.** The spec says
   auto-advance skips this between steps (auto-commit ensures cleanliness). Two
   options: (a) extract the invoke+commit logic into a function without the
   precondition and call it from auto-advance, or (b) keep calling `run()` as-is
   since auto-commit leaves the tree clean. Option (b) is simpler and correct:
   after each action's auto-commit, the tree *is* clean, so `run()`'s check passes.

3. **Arg satisfiability:** An action is auto-executable if `not action.human` and
   every name in `action.args` exists as a key in `task_context(root)`. The
   `evolve` action requires `target` which won't be in task context, so it's
   correctly skipped.

4. **`-p` and `--dry-run` must propagate.** These are currently per-action options
   on `_make_action_command`. For auto-advance, they need to be on the group
   itself (or passed through context). Since auto-advance constructs prompts
   directly, it can accept these as group-level options.

5. **Existing single-action path must be unchanged.** `neo do <action>` still
   routes through `DoGroup.get_command()` → `_make_action_command`.

## Implementation

### Step 1: Add `--dry-run` and `--prompt` options to `DoGroup`

Add `-p/--prompt` and `-n/--dry-run` as params on the `_do_group` instance,
alongside the existing `-w/--workflow`.

### Step 2: Override `DoGroup.invoke()` for auto-advance

Override `invoke()` on `DoGroup`. Click's `Group.invoke()` calls
`self.result_callback()` when there's no subcommand. Instead, we detect
whether `ctx.invoked_subcommand` is `None` after parsing and, if so,
run the auto-advance loop.

The cleanest Click-idiomatic approach: add a `@_do_group.result_callback()`
that receives the group-level params. But `DoGroup` is already a custom class,
so overriding `invoke()` is clearer.

Actually, the simplest approach: give `DoGroup` an `invoke` override that
checks `ctx.protected_params` / the parsed args. If no subcommand was given,
run auto-advance. Otherwise, delegate to `super().invoke()`.

Concretely:

```python
class DoGroup(click.Group):
    def invoke(self, ctx: click.Context) -> None:
        # Let Click parse; if there's a subcommand, delegate normally.
        # Click sets ctx.invoked_subcommand during invoke().
        # We need to check after parsing but before dispatching.
        # The standard pattern: override invoke, call parse_args, check.
        if not ctx.protected_params and not ctx.args:
            # No subcommand given → auto-advance
            _auto_advance(ctx)
            return
        super().invoke(ctx)
```

Wait — Click's `Group.invoke()` is what does the parsing. We need a different
approach. The right pattern for Click groups that have a default action:

```python
class DoGroup(click.Group):
    def parse_args(self, ctx, args):
        # If no args (or only options), note that we should auto-advance
        # Actually this is tricky because options like -n haven't been consumed yet
        ...
```

Simplest correct approach: override `invoke()`, let `super().invoke()` run,
and use `@_do_group.result_callback()` for the no-subcommand case.

Actually, re-reading Click source: `Group.invoke()` invokes the group callback
first (the function decorated with `@click.group()`), then looks at
`ctx.invoked_subcommand`. If it's `None`, it either invokes the result callback
or raises `UsageError`.

The cleanest pattern:

```python
_do_group = DoGroup("do", help="Execute a workflow action.", invoke_without_command=True)
```

With `invoke_without_command=True`, when no subcommand is given, Click calls the
group callback (if any) with `ctx.invoked_subcommand = None`, and does NOT show
help. We can attach a callback to `_do_group` that checks
`ctx.invoked_subcommand`:

```python
@_do_group.callback
@click.option("-p", "--prompt", ...)
@click.option("-n", "--dry-run", ...)
@click.pass_context
def _do_callback(ctx, prompt, dry_run, workflow):
    if ctx.invoked_subcommand is None:
        _auto_advance(ctx, prompt=prompt, dry_run=dry_run)
```

This is the standard Click pattern for "group with default action". The `-w`
option is already a param on `_do_group`; `-p` and `-n` get added here.

One concern: for `neo do <action> -p ...`, the `-p` must be on the subcommand,
not the group. Click handles this correctly if `-p` is defined on both: when a
subcommand is present, Click consumes group-level options first, then passes
remaining args to the subcommand. Since `-p` appears at both levels, we need the
group's `-p` to not consume the subcommand's `-p`. This is fine because Click
parses group options before the subcommand name.

But actually: `neo do -p "extra" research` vs `neo do research -p "extra"`. The
former puts `-p` on the group; the latter on the subcommand. Both work. In
auto-advance mode, there's no subcommand, so `-p` is unambiguously on the group.

### Step 3: Implement `_auto_advance()`

```python
def _auto_advance(ctx: click.Context, *, prompt: str | None, dry_run: bool) -> None:
    root = git.repo_root()
    wf = _get_workflow(ctx)
    verbose = _verbose(ctx)
    executed: list[str] = []

    while True:
        stage = wf.stage(root)
        tctx = task_context(root)
        actions = wf.next_actions(stage)
        runnable = [a for a in actions if _is_auto_runnable(a, tctx)]
        if not runnable:
            break

        for action in runnable:
            if verbose:
                click.echo(f"auto: {action.name} (stage: {stage})")
            rendered = action.render_prompt(tctx)
            if prompt and "{{user_prompt}}" not in action.prompt_template:
                rendered = f"{rendered}\n\nAdditional direction: {prompt}"
            elif prompt:
                tctx_with_prompt = {**tctx, "user_prompt": prompt}
                rendered = action.render_prompt(tctx_with_prompt)
            if dry_run:
                click.echo(f"--- {action.name} ---")
                click.echo(rendered)
                executed.append(action.name)
                continue
            run_mod.run(rendered)
            executed.append(action.name)

    stage = wf.stage(root)
    if executed:
        click.echo(f"done: {' → '.join(executed)} (stage: {stage})")
    else:
        click.echo(f"nothing to do (stage: {stage})")
```

Where:

```python
def _is_auto_runnable(action: Action, tctx: dict[str, str]) -> bool:
    if action.human:
        return False
    return all(arg in tctx for arg in action.args)
```

### Step 4: Handle `--dry-run` in auto-advance

In dry-run mode, no Claude invocations happen, so no files are created and
`infer_stage` won't advance. The loop would run forever on the same stage.
Fix: in dry-run mode, execute one iteration only (print all runnable actions
at current stage, then break).

Revised loop:

```python
    while True:
        stage = wf.stage(root)
        tctx = task_context(root)
        actions = wf.next_actions(stage)
        runnable = [a for a in actions if _is_auto_runnable(a, tctx)]
        if not runnable:
            break

        for action in runnable:
            ...
            executed.append(action.name)

        if dry_run:
            break
```

### Step 5: Handle action failure

`run_mod.run()` calls `raise SystemExit(returncode)` on non-zero exit. This
will propagate out of the loop and Click will handle it. That's correct per the
spec (stopping condition 4). The executed-so-far actions won't be reported,
but that's acceptable — the error message from `run()` is sufficient.

Actually, we should catch `SystemExit` to report progress before re-raising:

```python
        for action in runnable:
            ...
            try:
                run_mod.run(rendered)
            except SystemExit:
                if executed:
                    click.echo(f"failed at {action.name} after: {' → '.join(executed)}")
                raise
            executed.append(action.name)
```

## Summary of changes

| File | Change |
|------|--------|
| `_cli.py` | Add `invoke_without_command=True` to `DoGroup` constructor |
| `_cli.py` | Add `_do_group.callback` with `-p`, `-n` options |
| `_cli.py` | Add `_auto_advance()` function |
| `_cli.py` | Add `_is_auto_runnable()` helper |

No changes to `_run.py`, `_actions.py`, `_workflow.py`, or test files.

## Verification

### Running the tests

From the repo root:

```
uv run pytest tests/test_integration.py -x -v
```

The two auto-advance tests should pass:
- `test_do_no_args_auto_advances_through_bug_workflow`
- `test_do_no_args_stops_at_human_action`

All existing tests must continue to pass (no regressions).

### Manual verification

To confirm the tests are testing the right thing, the fix can be reverted and
the two auto-advance tests should fail:

```
git stash
uv run pytest tests/test_integration.py::test_do_no_args_auto_advances_through_bug_workflow tests/test_integration.py::test_do_no_args_stops_at_human_action -x
# Both should FAIL
git stash pop
```
