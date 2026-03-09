---
name: specify
args:
  - issue
---
Determine the type of reference given in {{issue}}:
- If it looks like a GitHub issue ref (#N, owner/repo#N, or a github URL),
  fetch it with `gh issue view {{issue}}`.
- If it looks like a JIRA key (e.g. PROJ-123), fetch it from JIRA.
- Otherwise treat it as a verbatim feature description.

Research all relevant parts of the codebase. Take the formal view that the
absence of this feature is a bug. Write a clear specification to .task/task.md.

Write a failing test that demonstrates the feature does not yet exist, using
realistic application usage. Save your analysis to .task/spec.md. Commit the
failing test.
