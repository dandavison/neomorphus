from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Action:
    name: str
    prompt_template: str
    human: bool = False

    def render_prompt(self, context: dict[str, str]) -> str:
        return self.prompt_template.format(**context)


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
