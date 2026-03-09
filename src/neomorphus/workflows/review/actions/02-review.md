---
name: review
---
Using .task/context.md:

{{context}}

Review the PR. First answer: who proposed this, why, and is the change the
right move? If not, stop and say so.

Then, unless impractical, independently attempt to make the same change
yourself without looking at their diff. Compare your approach with theirs:
did you do anything they did not, or vice versa?

Check for correctness, test coverage, simplicity, and whether the change is
well-executed. Write .task/review.md.
