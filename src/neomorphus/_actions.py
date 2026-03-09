import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml

_DEFAULT_ACTIONS_DIR = Path(__file__).parent / "workflows" / "default" / "actions"
_MUSTACHE_RE = re.compile(r"\{\{(\w+)\}\}")
_FRONTMATTER_RE = re.compile(r"\A---\n(.+?)\n---\n(.*)", re.DOTALL)


@dataclass(frozen=True)
class Action:
    name: str
    prompt_template: str
    human: bool = False
    args: tuple[str, ...] = ()

    def render_prompt(self, context: dict[str, str]) -> str:
        return _MUSTACHE_RE.sub(
            lambda m: context.get(m.group(1), m.group(0)),
            self.prompt_template,
        )


class Actions:
    """Namespace of actions loaded from a directory of markdown files.

    Actions are available as attributes (e.g. actions.plan).
    Iterating yields all actions.
    """

    def __init__(self, action_list: list[Action]) -> None:
        self._all = list(action_list)
        for a in action_list:
            setattr(self, a.name, a)

    def __getattr__(self, name: str) -> Action:
        raise AttributeError(f"no action named '{name}'")

    def __iter__(self) -> Iterator[Action]:
        return iter(self._all)


def load_action(path: Path) -> Action:
    text = path.read_text()
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1))
    prompt = m.group(2).strip()
    return Action(
        name=meta["name"],
        prompt_template=prompt,
        human=meta.get("human", False),
        args=tuple(meta.get("args", ())),
    )


def load_actions(directory: Path | None = None) -> Actions:
    d = directory or _DEFAULT_ACTIONS_DIR
    return Actions([load_action(p) for p in sorted(d.glob("*.md"))])


def task_context(root: Path) -> dict[str, str]:
    ctx: dict[str, str] = {}
    task_dir = root / ".task"
    if not task_dir.is_dir():
        return ctx
    for p in sorted(task_dir.glob("*.md")):
        ctx[p.stem] = p.read_text()
    plans_dir = task_dir / "plans"
    if plans_dir.is_dir():
        plans = sorted(plans_dir.glob("*.md"))
        for p in plans:
            ctx[f"plan_{p.stem}"] = p.read_text()
        ctx["plans_summary"] = "\n\n".join(
            f"--- Plan {p.stem} ---\n{p.read_text()}" for p in plans
        )
        ctx["next_plan_number"] = str(len(plans) + 1)
    else:
        ctx["next_plan_number"] = "1"
    return ctx
