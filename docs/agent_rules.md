# Agent Rules

These rules define how the first YouTube fandom agent should answer questions and use feedback.

## Data Usage

- Prefer modeled tables for analysis: `fact_videos`, `dim_categories`, `dim_topics`, `fact_video_tags`, and `fact_video_topics`.
- Use `videos` and `youtube_categories` as source/staging tables only.
- Only run read-only SQL for question answering.
- Do not use tables, columns, joins, or metrics that are not documented in `docs/schema.md` or `docs/semantic_model.md`.
- When a query can return many rows, add a clear `LIMIT`.

## Answer Format

Each agent answer should include:

- A direct answer to the user's question.
- The SQL used, at least during development and evaluation.
- A short self-check.
- Any important data limitations.

## Self-Check

The self-check should answer:

- Did the available data fully, partially, or not at all support the answer?
- Which table grain was used?
- Were joins needed, and if so, were they one-to-one or one-to-many?
- Are there nulls, duplicates, broad categories, or point-in-time metrics that affect interpretation?

Use these support levels:

- `supported`: the answer follows directly from the available tables.
- `partially_supported`: the answer uses available data but requires interpretation or a proxy.
- `unsupported`: the current database does not contain the data needed to answer.

## Uncertainty

- Do not infer fan sentiment from `commentCount`; the database does not include comment text.
- Do not treat YouTube tags as exhaustive; many videos have no tags.
- Do not treat broad YouTube categories as fandom-specific labels.
- Do not imply that view, like, or comment counts are current; they are snapshots from fetch time.
- If a question asks for unavailable data, say what is missing and what related data exists.

## Human Feedback Loop

Human review does not update model weights directly. When a human reviewer identifies an error, missing context, or recurring failure pattern, update one or more system artifacts before rerunning the eval:

- `docs/schema.md`
- `docs/semantic_model.md`
- `docs/gotchas.md`
- agent prompt/instructions
- eval questions
- few-shot examples
- agent code/tests

The agent should improve through changes to these artifacts, then be re-evaluated against the same or expanded eval set.

## Evaluation Scores

Human reviewers should score answers on:

- Correctness: whether the answer is actually right.
- Groundedness: whether the answer used the database, schema, joins, and metrics properly.
- Self-awareness: whether the answer accurately described how well the data supported the answer.
