The _Neomorphus_ Ground-Cuckoos are rarely-seen birds that follow ant swarms in Amazonian forests.

<p align="center">
  <img src="./etc/Neomorphus-geoffroyi.png" alt="Neomorphus geoffroyi" width="400">
  <br>
  <span style="font-size: small; color: gray;"><i>Neomorphus geoffroyi</i> (Rufous-vented Ground-Cuckoo)</span>
</p>

Neomorphus (`neo` on the command line) is also a framework for defining agentic AI workflows. It's
just an early experimental prototype: not ready for use. It has two key principles:

1. AI agents are intelligent and can carry out complex tasks. However, for non-trivial projects we
   will often want to enforce that the entire project is broken down into stages (a "workflow"),
   with each stage being done by an agent. We want to enforce that workflow ourselves, rather than
   describing it to an agent and hoping it follows it faithfully.

2. The human user will often want to participate in some of these stages of work, so that they
   acquire understanding of the design and implementation, rather than leaving it all to human
   review stages.

The basic idea of working with `neo` is:

- You specify a workflow defining how an AI agent will collaborate with you to do task definition,
  planning, implementation, review, etc.

- The file system is the point of truth. At any point (any git commit) `neo` can determine what
  stage you're at by the presence/absence of certain special files (task definition, plans, etc).

- `neo` knows the available next actions given the current task state. It can generate a prompt for
  an agent to carry them out, and it can have the agent do it, in collaboration with you, or
  automatically.

## Custom workflows

Run `neo init` to scaffold a `.neo/` directory, then edit the files to define your workflow.
A workflow is a state machine: stages inferred from the filesystem, connected by actions (prompts
sent to an AI agent). Here are two examples.

### Example: issue workflow

A workflow for working on issues: reproduce, plan, implement, verify.

```
.neo/
├── workflow.py
└── actions/
    ├── repro.md
    ├── plan.md
    ├── implement.md
    └── verify.md
```

`.neo/workflow.py`:
```python
from pathlib import Path
from neomorphus import Stage, Workflow, load_actions

OPEN       = Stage("open")
REPRODUCED = Stage("reproduced")
PLANNED    = Stage("planned")
DONE       = Stage("done")

actions = load_actions(Path(__file__).parent / "actions")

def infer_stage(root: Path) -> Stage:
    if (root / ".task/result.md").exists():
        return DONE
    if (root / ".task/plan.md").exists():
        return PLANNED
    if (root / ".task/repro.md").exists():
        return REPRODUCED
    return OPEN

workflow = Workflow(
    transitions={
        OPEN:       {actions.repro: REPRODUCED},
        REPRODUCED: {actions.plan: PLANNED},
        PLANNED:    {actions.implement: DONE},
        DONE:       {actions.verify: DONE},
    },
    infer_stage=infer_stage,
)
```

The action prompts are markdown files with YAML frontmatter. They can reference files via
`{{mustache}}` variables — `neo` reads `.task/` files into the template context automatically.

`.neo/actions/repro.md`:
```markdown
---
name: repro
---
Read .task/task.md. Write a failing test that reproduces the bug.
Save your analysis to .task/repro.md.
```

`.neo/actions/plan.md`:
```markdown
---
name: plan
---
Given the reproduction in .task/repro.md:

{{repro}}

Propose an implementation plan. Write it to .task/plan.md.
```

`.neo/actions/implement.md`:
```markdown
---
name: implement
---
Implement the fix described in .task/plan.md:

{{plan}}

Write .task/result.md summarising what you changed and why.
```

`.neo/actions/verify.md`:
```markdown
---
name: verify
---
Review the implementation. Run the tests. Confirm the repro test now passes.
Update .task/result.md with verification status.
```

Usage:
```
$ neo status
stage: open

$ neo next
stage: open
  repro: $ neo do repro

$ neo do repro
# agent writes failing test, saves .task/repro.md

$ neo do plan
# agent reads repro, writes .task/plan.md

$ neo do implement
# agent implements the fix

$ neo do verify
# agent runs tests, confirms fix
```

### Example: PR review workflow

A workflow for reviewing pull requests: first build context, then review.

```
.neo/
├── workflow.py
└── actions/
    ├── contextualize.md
    └── review.md
```

`.neo/workflow.py`:
```python
from pathlib import Path
from neomorphus import Stage, Workflow, load_actions

PENDING  = Stage("pending")
REVIEWED = Stage("reviewed")

actions = load_actions(Path(__file__).parent / "actions")

def infer_stage(root: Path) -> Stage:
    if (root / ".task/review.md").exists():
        return REVIEWED
    return PENDING

workflow = Workflow(
    transitions={
        PENDING:  {actions.contextualize: PENDING, actions.review: REVIEWED},
        REVIEWED: {actions.review: REVIEWED},
    },
    infer_stage=infer_stage,
)
```

`.neo/actions/contextualize.md`:
```markdown
---
name: contextualize
args:
  - pr_url
---
Fetch the PR at {{pr_url}}. Identify what the author is trying to achieve.
Understand the surrounding code. Write your analysis to .task/context.md.
```

`.neo/actions/review.md`:
```markdown
---
name: review
---
Using .task/context.md:

{{context}}

Review the PR. Check for correctness, test coverage, simplicity, and
whether the change is the right move. Write .task/review.md.
```

Usage:
```
$ neo do contextualize https://github.com/org/repo/pull/123
# agent fetches PR, writes .task/context.md

$ neo do review
# agent reviews against context, writes .task/review.md
```