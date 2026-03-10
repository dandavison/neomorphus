# Feature: `neo do` auto-advance mode

## Summary

`neo do` (invoked with no action argument) should automatically advance through the
workflow graph as far as possible, stopping only when blocked on a human action (or
when no actions are available). When traversing the graph, steps whose dependencies
are all met should be executed concurrently.

## Current behaviour

`neo do` with no subcommand displays Click group help text and exits.

## Desired behaviour

`neo do` (no action name):
1. Infer current stage.
2. Identify available non-human actions that can be auto-executed (no required args
   that aren't already present in task context).
3. If multiple such actions exist at the current stage, execute them concurrently.
4. After all concurrent actions complete, re-infer stage.
5. Repeat from (1) until: no actions available, only human actions remain, or all
   remaining actions require user-supplied arguments.
6. Report what was executed and the final stage.

Actions that require positional arguments not present in task context cannot be
auto-executed and are treated as blocking (same as human actions).

## Scope

- Core: sequential auto-advance through linear workflows (bug, feature, refactor)
- Core: stop at human actions
- Core: skip actions with unsatisfied required args
- Stretch: concurrent execution when multiple independent actions are available
