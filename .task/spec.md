# Spec: `neo do` auto-advance

## Behaviour

When `neo do` is invoked without an action name, it enters auto-advance mode:

```
loop:
  stage = infer_stage(root)
  actions = non-human actions at stage with all required args satisfiable from task context
  if actions is empty: break
  execute actions concurrently (each via invoke_claude + auto-commit)
  # stage is re-inferred from filesystem on next iteration
report actions executed and final stage
```

## Execution model

Each action execution is: render prompt → invoke Claude → auto-commit if changes.
This is the same as `neo do <action>` today, but without the clean-tree precondition
between steps (the auto-commit after each step ensures the tree is clean for the next).

When multiple actions are eligible at a stage, they run concurrently. Each gets its
own Claude invocation. Since they start from the same filesystem state and each
auto-commits, concurrent execution requires care: the actions must not conflict.
For the initial implementation, concurrent actions can be run sequentially (simpler);
true concurrency is a follow-up.

## Stopping conditions

1. No actions available at current stage (terminal stage or no outgoing edges).
2. All available actions are human actions.
3. All available non-human actions require positional args not present in task context.
4. An action fails (Claude exits non-zero).

## CLI surface

- `neo do` (no args) → auto-advance mode
- `neo do <action>` → unchanged (single action execution)
- Auto-advance respects `-w`, `--dry-run`, `-p` (applied to all actions), `-v`.

## Arg satisfiability

An action's required args are satisfiable if every arg name exists as a key in the
task context dict (built from `.task/*.md` files). For example, `evolve` requires
`target` which is not a `.task/` file stem, so it's unsatisfiable and skipped.

## Output

In verbose mode, report each action as it starts and completes.
In normal mode, report the sequence of actions executed and final stage.
