# How the AI engine works

When I started designing how Triage should decide who gets a task, the first instinct was to just ask an LLM. Give it the task description, give it the list of team members, and let it figure it out. That approach has an obvious problem: you can't test it, you can't explain it, and you can't trust it to be consistent.

So I split the problem into two clearly defined phases: a deterministic scoring phase that produces a ranked list of candidates, and a reasoning phase where the LLM's only job is to explain a decision that has already been made.

## Why I didn't follow the standard RAG pattern

In a standard RAG system the flow looks like this:
1. Retrieve relevant chunks from a vector DB based on semantic similarity.
2. Pad those chunks with extra context and pass everything to the LLM.
3. The LLM generates a response.

The LLM is doing the heavy lifting in step 3, which means it's also the source of any inconsistency. I wanted scoring to be a function with deterministic outputs — something I could write unit tests against without mocking an AI model. So I reworked the pipeline.

## Phase 1: Retrieval

When a new testable arrives, I query the vector DB for the top 10 semantically similar historical testables. These aren't just used for context — each historical testable has associated team members who worked on it, and that association gets pulled along with it.

The retrieval is filtered by team metadata so that cross-team escalation doesn't happen by accident. If a task genuinely needs someone from another team, there's a mechanism to widen that filter, but by default it stays scoped to the relevant squad.

## Phase 2: Scoring (the decoupled part)

Instead of passing the retrieved documents to an LLM, I use the cosine similarity scores — the vector distances from the retrieval step — to calculate an expertise score for each associated team member. That expertise score feeds into a mathematical constraint scorer.

The constraint scorer takes expertise as one input among several: things like current workload, recent assignment history, and skill tags. It produces a composite score and a final ranking.

This entire phase has no LLM calls. It's pure math, which means it's straightforward to unit test. Given the same inputs, you always get the same ranking. That predictability was important to me — the assignment decision needed to be something I could audit and explain to my team, not a black box.

## Phase 3: Reasoning

Once the ranking is finalized, I pass it to an LLM along with the task description and the top candidate's score breakdown. The LLM generates a short explanation of why that engineer was assigned this particular task. It's reading a decision that was already made and writing a justification for it, which is a much more constrained and reliable use of a language model.

The result is that an assigned engineer doesn't just see "you've been assigned STRY-4521" — they see something that actually explains the reasoning.

## Future improvements: hybrid retrieval

The current retrieval is purely semantic. One thing I want to add is hybrid retrieval that combines semantic search with lexical search. A lot of task descriptions reference specific story or defect IDs (e.g., `STRY-1234`, `DEF-9876`) and right now those references don't carry extra weight. Using regex to extract those IDs and running a targeted lexical search alongside the semantic search would let the system pick up direct references to past work, which should improve accuracy meaningfully in cases where someone is working on a follow-up to a known bug.
