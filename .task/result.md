# Result: `neo do` auto-advance mode

## What changed

Single file modified: `src/neomorphus/_cli.py`.

### `DoGroup` now accepts `invoke_without_command=True`

When no subcommand is given, Click calls the group callback instead of showing
help.

### Group callback `_do_callback`

Attached via `_do_group.callback = _do_callback` with `-p/--prompt` and
`-n/--dry-run` options. When `ctx.invoked_subcommand is None`, delegates to
`_auto_advance()`.

### `_auto_advance()`

Loop:
1. Infer stage, build task context, get next actions.
2. Filter to auto-runnable actions (non-human, args satisfiable, not a
   self-loop).
3. Execute each via `run_mod.run()` (which invokes Claude and auto-commits).
4. Re-infer stage; if unchanged, break (handles self-loops like verify→verify).
5. In dry-run mode, print rendered prompts and break after one iteration.

On failure (`SystemExit` from `run()`), reports progress before re-raising.

### `_is_auto_runnable()`

An action is auto-runnable if:
- Not a human action.
- Its target stage differs from the current stage (skip self-loops).
- All required args exist in the task context dict.

## Design decisions

- **Self-loop detection:** The bug workflow has `DONE → verify → DONE`. Rather
  than running verify forever, `_is_auto_runnable` skips actions whose target
  stage equals the current stage. A secondary guard (`new_stage == stage` after
  execution) catches any remaining non-progress scenarios.

- **No changes to `_run.py`:** Per the plan, `run()`'s clean-tree precondition
  is satisfied between steps because each step auto-commits.

- **`-p` and `-n` at both levels:** These options exist on both the group
  (for auto-advance) and on individual action subcommands. Click's parsing
  handles this correctly: group options are consumed before the subcommand name.

## Verification

```
uv run pytest tests/test_integration.py -x -v
```

Both auto-advance tests pass:
- `test_do_no_args_auto_advances_through_bug_workflow` — runs research → plan →
  implement through the bug workflow, confirms 3 Claude calls and final stage DONE.
- `test_do_no_args_stops_at_human_action` — default workflow at no-task stage
  has only the human `init` action; confirms zero Claude calls.

All 54 tests pass with no regressions.
