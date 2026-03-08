import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_MUSTACHE_RE = re.compile(r"\{\{(\w+)\}\}")
_FRONTMATTER_RE = re.compile(r"\A---\n(.+?)\n---\n(.*)", re.DOTALL)


@dataclass(frozen=True)
class Action:
    name: str
    prompt_template: str
    human: bool = False
    interactive: bool = False
    args: tuple[str, ...] = ()

    def render_prompt(self, context: dict[str, str]) -> str:
        return _MUSTACHE_RE.sub(
            lambda m: context.get(m.group(1), m.group(0)),
            self.prompt_template,
        )


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
        interactive=meta.get("interactive", False),
        args=tuple(meta.get("args", ())),
    )


def load_actions(directory: Path | None = None) -> list[Action]:
    d = directory or _PROMPTS_DIR
    return [load_action(p) for p in sorted(d.glob("*.md"))]


def task_context(root: Path) -> dict[str, str]:
    ctx: dict[str, str] = {}
    task_file = root / ".task" / "task.md"
    if task_file.is_file():
        ctx["task"] = task_file.read_text()
    plan_file = root / ".task" / "plan.md"
    if plan_file.is_file():
        ctx["plan"] = plan_file.read_text()
    plans_dir = root / ".task" / "plans"
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
