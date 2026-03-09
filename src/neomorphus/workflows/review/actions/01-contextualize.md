---
name: contextualize
args:
  - pr_ref?
---
First, update the current branch from the remote: run `git pull --ff-only`.
If that fails, stop with an error.

Find the PR to review:
- If a reference was provided ({{pr_ref}}), use `gh pr view {{pr_ref}} --json url,title,body,baseRefName,headRefName,files,commits`.
- Otherwise run `gh pr view --json url,title,body,baseRefName,headRefName,files,commits`
  to find the open PR for the current branch.
If no PR is found, stop with an error.

Fetch the full diff with `gh pr diff`. Identify what the author is trying to
achieve. Understand the surrounding code. Write your analysis to
.task/context.md.
