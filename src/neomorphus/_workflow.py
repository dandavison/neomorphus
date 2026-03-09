from __future__ import annotations

import importlib.util
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from neomorphus._actions import Action
from neomorphus._status import Stage


@dataclass(frozen=True)
class Workflow:
    transitions: dict[Stage, dict[Action, Stage]]
    infer_stage: Callable[[Path], Stage]
    _stages: frozenset[Stage] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        stages: set[Stage] = set()
        for src, edges in self.transitions.items():
            stages.add(src)
            for _action, dst in edges.items():
                stages.add(dst)
        object.__setattr__(self, "_stages", frozenset(stages))

    def stage(self, root: Path) -> Stage:
        result = self.infer_stage(root)
        if result not in self._stages:
            raise ValueError(f"infer_stage returned unknown stage: {result}")
        return result

    def next_actions(self, stage: Stage) -> list[Action]:
        return list(self.transitions.get(stage, {}))

    def action(self, name: str) -> Action | None:
        for edges in self.transitions.values():
            for action in edges:
                if action.name == name:
                    return action
        return None

    def target_stage(self, current: Stage, action_name: str) -> Stage | None:
        edges = self.transitions.get(current, {})
        for action, dst in edges.items():
            if action.name == action_name:
                return dst
        return None

    def _transitions(self) -> Iterator[tuple[Stage, str, Stage]]:
        seen: set[tuple[str, str, str]] = set()
        for stage, edges in self.transitions.items():
            for action, target in edges.items():
                key = (stage.name, action.name, target.name)
                if key not in seen:
                    seen.add(key)
                    yield stage, action.name, target

    def diagram_mermaid(self) -> str:
        lines = ["stateDiagram-v2"]
        for src, action_name, dst in self._transitions():
            lines.append(f"    {src} --> {dst}: {action_name}")
        return "\n".join(lines)

    def diagram_d2(self) -> str:
        lines = []
        for src, action_name, dst in self._transitions():
            lines.append(f"{src} -> {dst}: {action_name}")
        return "\n".join(lines)


def load_workflow(root: Path, name: str | None = None) -> Workflow:
    neo_dir = root / ".neo"
    if not neo_dir.is_dir():
        if name is not None:
            raise ValueError(f".neo/ not found in {root}")
        from neomorphus.workflows.default import DEFAULT_WORKFLOW

        return DEFAULT_WORKFLOW

    if name is not None:
        return _load_custom_workflow(_resolve_workflow_file(root, name))

    workflows = _discover_workflows(neo_dir)
    if len(workflows) == 0:
        raise ValueError(f".neo/ exists but contains no workflows in {root}")
    if len(workflows) > 1:
        names = ", ".join(sorted(n for n, _ in workflows))
        raise ValueError(f"multiple workflows found ({names}). Use -w to select.")
    return _load_custom_workflow(workflows[0][1])


def _resolve_workflow_file(root: Path, name: str) -> Path:
    if "/" in name or name.endswith(".py"):
        p = Path(name) if Path(name).is_absolute() else root / name
        if not p.is_file():
            raise ValueError(f"workflow file not found: {p}")
        return p
    wf_file = root / ".neo" / name / "workflow.py"
    if not wf_file.is_file():
        raise ValueError(f"workflow '{name}' not found at {wf_file}")
    return wf_file


def _discover_workflows(neo_dir: Path) -> list[tuple[str, Path]]:
    results: list[tuple[str, Path]] = []
    for child in sorted(neo_dir.iterdir()):
        if child.is_dir():
            wf_file = child / "workflow.py"
            if wf_file.is_file():
                results.append((child.name, wf_file))
    return results


def _load_custom_workflow(wf_file: Path) -> Workflow:
    import sys

    spec = importlib.util.spec_from_file_location("_neo_workflow", wf_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {wf_file}")
    mod = importlib.util.module_from_spec(spec)
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    wf = getattr(mod, "workflow", None)
    if not isinstance(wf, Workflow):
        raise ValueError(f"{wf_file} must define a 'workflow' variable of type Workflow")
    return wf
