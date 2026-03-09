---
name: research
args:
  - issue
---
Determine the type of reference given in {{issue}}:
- If it looks like a GitHub issue ref (#N, owner/repo#N, or a github URL),
  fetch it with `gh issue view {{issue}}`.
- If it looks like a JIRA key (e.g. PROJ-123), fetch it from JIRA.
- Otherwise treat it as a verbatim bug description.

Research all relevant parts of the codebase thoroughly. Write a clear
description of the bug to .task/task.md.

Next, attempt to reproduce the bug: create a failing test that demonstrates it
realistically (trigger the bug through normal application usage, not by
importing internals). Save your analysis and repro details to .task/repro.md.
Commit the failing test.
