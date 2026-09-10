# Learning Log

This file records project decisions, why they were made, and questions to check understanding over time.

Use it when the project changes direction, when an eval reveals a repeated failure, or when a concept feels fuzzy enough that it deserves a plain-language note.

## How To Use This File

- Add a short entry when you make a meaningful design decision.
- Include why the decision was made, not just what changed.
- Add one or two check-your-understanding questions.
- Revisit old entries after evals to see whether the decision still holds.

## Review Feedback Loop

Human review lives in files like:

```text
evals/reviews/simple_sql_agent_v1_review.md
```

When you fill in review scores and notes, use them to decide what should change next:

| Review finding | Update |
| --- | --- |
| Agent used the wrong table or grain | `docs/schema.md`, `docs/semantic_model.md`, agent code/tests |
| Agent used a metric incorrectly | `docs/semantic_model.md`, agent code/tests |
| Agent missed an important caveat | `docs/gotchas.md`, `docs/agent_rules.md` |
| Agent was overconfident | `docs/agent_rules.md`, prompts, tests |
| Eval question was unclear | `evals/questions_v1.json` |
| Agent needs a new capability | agent code/tests, then docs |
| Review shows a repeated concept gap | Add a decision or concept note in this file |

The model does not learn directly from your review file. The system improves when you turn review notes into updates to docs, eval questions, prompts, code, or tests.

## Decision Log

### 2026-09-09: Keep V1 Agent Deterministic

Decision: The first question-answering agent is a deterministic SQL agent instead of an LLM SQL agent.

Why: This creates a golden-query baseline. If this agent fails, the issue is probably schema, SQL, data, formatting, or tests. If this agent works but a later LLM agent fails, the issue is probably query planning, SQL generation, reasoning, or self-checking.

Check your understanding:

- What kinds of questions can a deterministic SQL agent answer well?
- What kinds of questions require an LLM or human judgment?

### 2026-09-09: Use SQL Before RAG

Decision: V1 uses SQLite queries as the retrieval layer. RAG is deferred.

Why: The current dataset is structured. Metrics like counts, averages, medians, tags, topics, and categories are better answered with SQL than vector search. RAG becomes useful later for unstructured sources like transcripts, comments, articles, notes, or human review examples.

Check your understanding:

- Why is SQL the right retrieval layer for the current data?
- What new data would make RAG useful?

### 2026-09-09: Separate Machine Results From Human Review

Decision: Eval results are written as JSONL, and human review is exported to Markdown.

Why: JSONL is good for programs because each line is one complete result. Markdown is better for humans because it is readable and easy to annotate with scores and notes.

Follow-up decision: Review exports should not overwrite an existing Markdown
review file by default. Human scores and notes are durable feedback, while eval
JSONL is generated output. To replace a review file intentionally, use the
exporter's `--overwrite` option.

Check your understanding:

- Why is `evals/results/simple_sql_agent_v1.jsonl` hard to review directly?
- What does `evals/reviews/simple_sql_agent_v1_review.md` add?
- Why should review Markdown be protected more carefully than result JSONL?

### 2026-09-09: Treat Review Notes As System Updates

Decision: Human feedback should update system artifacts, not model weights.

Why: The current project is not fine-tuning a model. It improves through clearer docs, better semantic definitions, stronger gotchas, better eval questions, prompts, code, and tests.

Check your understanding:

- If the agent forgets to mention missing comment text, which docs should change?
- If the agent writes the wrong SQL join, what should change?

### 2026-09-09: Split Unsupported Into Data vs Agent Limits

Decision: Eval review should distinguish `unsupported_by_data` from `unsupported_by_agent`.

Why: Some refusals are correct because the database lacks the data, like comment text or sentiment labels. Other refusals are only current-agent limitations, like not yet having a handler for channel average views. Treating both as just "unsupported" hides what should be fixed next.

Check your understanding:

- Which is it when the agent cannot answer "what are fans saying in comments"?
- Which is it when the agent cannot answer "which channels have the highest average views"?

### 2026-09-09: Clarify Broad Type Questions

Decision: Questions about "kind" or "type" of video should trigger clarification or a proxy-based answer.

Why: The database does not have a true video-type label. It has categories, topics, and tags. Those can be useful proxies, but the agent should name the proxy instead of acting like the label is directly observed.

Check your understanding:

- If a user asks what "types of videos" are most common, what clarification could the agent ask?
- If the agent answers without clarification, which proxy dimensions should it name?

## Concepts To Revisit

- Golden-query baseline
- SQL agent vs LLM SQL agent
- RAG vs structured retrieval
- Answer correctness vs groundedness vs self-awareness
- Supported vs partially supported vs unsupported answers
- Unsupported by data vs unsupported by current agent capability
- Broad type questions and proxy dimensions
- Human review as feedback into docs/evals/code
