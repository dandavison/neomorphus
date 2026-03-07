In this repo I'm considering starting a new project: it's going to be some sort of tool for AI-assisted software development. Here are my thoughts so far:


I'll define some sort of workflow: I won't rely on the agent to follow a workflow defined in its
prompt / skills.

So, this tool will provide a CLI to answer questions and perform actions with reference to that user-defined workflow.

At any point I can use the CLI to essentially compute infer_stage(repo@commit, workflow_defn). This
will look at the filesystem state at that commit and, according to the presense/absence/contents of
certain special files, infer what stage the task is at. For example, perhaps we have
.task/plans/1.md, .task/plans/2.md (proposed plans awaiting LLM-as-a-judge or human selection) and
.task/plan.md (the chosen plan). If neither exist we haven't started planning; if the latter exists
then we've finished planning; if the former but not the latter exist then we're at plan-selection
stage.


So the point-of-truth for the stage of a commit is the filesystem state at that commit: I'm
considering that rather than separately persisting the stage that the state machine has got to.


At some point, this tool is going to ask a coding agent (claude code) to do something. Let's say
that all changes must be committed at that point. So that's essentially a function
do_something(repo@commit, prompt, skills). It might take place locally or on a remote machine.


I think a bit I don't yet have clear ideas about, and perhaps the core of the whole thing is how do
we define "workflows"? Let me paint a picture of one possible workflow I'm imagining:

> The first stage is plan-generation. Our aim is, for each of one or more prompts given by the user,
> to propose N alternative designs/plans to achieve the task specified in the prompt. Next, we
> either use agents to propose which plan should be selected, or a human does so. We thus reach
> plan-selected stage. In the next stage (implementation-generation) we do something analogous:
> produce M competing implementations of the next phase, before using LLM-as-a-judge or human to
> select one of them. But at this stage also the human can elect to enter collaborative mode (see
> below).

So... we're defining a state machine. We want to be able to ask what the possible next actions are.
And for any selected action we need to know how to invoke do_something(repo@commit, prompt, skills)
as appropriate for that action.


Criteria for evaluating implementations include:
- Is it correct?
- Is it suboptimal from security / performance POVs?
- Is the code well-engineered? (Builds appropriately on existing code, refactors where necessary,
  extensible, avoids duplication, elegant and readable by humans, uses/introduces abstractions
  appropriately, not too many more LOC than necessary etc)

A fundamental objective for this project is that it very explicitly exposes ways for the human user
to participate and thus acquire knowledge and understanding of the design and software mechanics in
the way that they did in the pre-agentic days of "classical programming". So, for example, at
implementation stage, the human might choose to work collaboratively with the AI: the AI starts off
"I think we might want to create these classes in these files; here's a start"; the human does some
work on these and says "OK, I've advanced it a bit, what do you think?" (a commit is always made
before the AI does anything); the AI says "I had a look and left some comments in the code; PTAL";
the human says "OK I addressed your comments and did some more. If this LGTY can you complete this
stage?"

I think what I've written so far also implies that we need get_next_actions(repo@commit,
workflow_defn).


As a sort of project "north star" we can bear in mind the idea that AI-assisted software devlopment
can in principle be viewed as an optimization problem: e.g. "out of all possible plans, find the
best one", or "given this plan, find the best out of all possible implementations". Of course I'm
not for a moment suggesting we formally define let alone solve that optimisation problem. But still,
it points to considerations which might be underesplored by current competing approaches such as the
idea that variance can be partitioned into "agentic variance" (given a prompt and available
skills/resources what it the variance of agent outputs?) and "human variance" (given a desire or
concept, what is the variance of prompts and skills/resources that a human makes available to an
agent that it is hoping will achieve that desire?). So, we might want the tool to allow the user to
say "generate 2 more plans using the same prompt", etc.

This whole thing needs to be kept fairly minimal and pragmatic to start off with. I'm not trying to build a magic black box that can produce complax software; I'm trying to build a tool that I can start using ASAP (hopefully "self-hosting"!); I absolutely must be able to tinker with the workflow details as we're going (hence my instinct that point-of-truth is git).