---
name: validate
args:
  - description
---
Proposed refactoring: {{description}}

A refactor must have no functional consequences. Before proceeding, verify that
the test suite is adequate: make some deliberately incorrect changes along the
lines of this refactoring and confirm that tests fail. If they don't, add tests
until they do, and commit those tests.

Write .task/task.md describing the proposed refactoring and .task/validation.md
documenting which deliberate breakages you tried and which tests caught them.
