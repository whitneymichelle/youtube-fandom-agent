# Simple SQL Agent V1 Review

Source results: `evals/results/simple_sql_agent_v1.jsonl`

Score each answer after reading the question, answer, SQL, self-check, and limitations.

Scoring:

- Correctness: `0` wrong/unsupported, `1` partially correct, `2` correct but thin, `3` correct and well-supported
- Groundedness: `0` not grounded, `1` weakly grounded, `2` mostly grounded, `3` properly grounded in schema/results
- Self-awareness: `0` overconfident/wrong, `1` vague, `2` mostly aware but incomplete, `3` accurately states support or limits

When feedback reveals a recurring failure, update the relevant system artifact: `docs/schema.md`, `docs/semantic_model.md`, `docs/gotchas.md`, `docs/agent_rules.md`, eval questions, examples, agent code, or tests.

## Review Summary

This review shows the golden-query agent is strongest when the question maps directly to an existing handler or a known data limitation.

Main follow-ups:

- Add a handler for channel average views. The agent already has similar ranking logic for most-viewed videos and category/topic average views.
- Add a handler for tag average views and tagged-vs-untagged average view comparisons.
- Clarify in `docs/agent_rules.md` that broad "kind/type of video" questions should either ask a clarifying question or answer with explicit proxy dimensions such as category, topic, tag, title, or channel.
- Track the difference between "unsupported because the data cannot answer this" and "unsupported because the V1 deterministic agent has no handler yet."
- Use `0-3` as the self-awareness score scale so it matches correctness and groundedness.

## q016: Which tags are associated with the highest average view count?

- Difficulty: `medium`
- Answer type: `grouped`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q018: Which channels have the highest average view count?

- Difficulty: `medium`
- Answer type: `grouped`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Human Review

- Correctness: 2
- Groundedness: 2
- Self-awareness: 0
- Notes:
- Follow-up artifact updates: Add a `channels by average views` handler in `src/agents/simple_sql_agent.py`; add a test in `tests/test_simple_sql_agent.py`; document the small-sample caveat in `docs/gotchas.md` or `docs/agent_rules.md`.

## q020: Do videos tagged with 'heated rivalry' have higher average views than videos without that tag?

- Difficulty: `medium`
- Answer type: `comparison`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q021: What kinds of Heated Rivalry videos seem most common in this dataset?

- Difficulty: `hard`
- Answer type: `synthesis`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Human Review

- Correctness: 2
- Groundedness: 2
- Self-awareness: 0
- Notes: could have followed up with what do you mean by 'type of video' to see if meant 'tags', 'categories', etc.
- Follow-up artifact updates: Update `docs/agent_rules.md` so broad "kind/type" questions trigger a clarifying question or an explicit proxy-based answer using categories, topics, tags, title, and channel.

## q022: What kinds of videos seem to perform best by view count?

- Difficulty: `hard`
- Answer type: `synthesis`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Human Review

- Correctness: 2
- Groundedness: 2
- Self-awareness: 0
- Notes: could have followed up with what do you mean by 'kinds of video' to see if meant 'tags', 'categories', etc.
- Follow-up artifact updates: Update `docs/agent_rules.md` with the same broad "kind/type" clarification rule; consider adding proxy-based synthesis examples to `docs/semantic_model.md`.

## q023: Are official clips or fan-created videos performing better?

- Difficulty: `hard`
- Answer type: `synthesis`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Expected Limitation

The database does not have an official/fan-made label, so any answer must explain the proxy used.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q024: What should we be careful about when interpreting the top-viewed videos?

- Difficulty: `hard`
- Answer type: `limitation`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

I do not have a supported query pattern for that question yet.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Unsupported by this V1 deterministic agent. Add a new handler or use a later LLM SQL-generation pass.

### Limitations

- This baseline only answers predefined SQL and answerability patterns.

### Expected Limitation

View counts are point-in-time snapshots and may reflect age, channel size, platform recommendation, or unrelated uses of the search phrase.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q025: Can we tell what fans are saying in the comments?

- Difficulty: `hard`
- Answer type: `answerability`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

No. The database has `commentCount`, but it does not contain comment text, so it cannot answer what fans are saying.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Correctly unsupported: comment content is not in the schema.

### Limitations

- Only comment counts are available.

### Expected Limitation

The database has comment counts but not comment text, so it cannot answer comment content or sentiment.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q026: Can we infer fan sentiment from comment counts?

- Difficulty: `hard`
- Answer type: `answerability`
- Requires human review: `True`
- Support level: `unsupported`

### Agent Answer

No. Comment counts measure engagement volume, not whether the comments are positive, negative, or mixed.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Correctly unsupported: sentiment needs comment text or labels.

### Limitations

- The database does not include comment text or sentiment labels.

### Expected Limitation

Comment counts show engagement volume, not sentiment.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q027: Can we identify whether a video is a reaction, recap, edit, trailer, or official clip?

- Difficulty: `hard`
- Answer type: `answerability`
- Requires human review: `True`
- Support level: `partially_supported`

### Agent Answer

Only partially. The database has title, description, channel, tags, categories, and topics, but no explicit content-type label.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Partially supported: the answer would require heuristic labels from metadata.

### Limitations

- No explicit official/fan/reaction/recap/edit/trailer label exists.

### Expected Limitation

The database has title, description, channel, tags, category, and topics, but no explicit content-type label.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:

## q030: What are the main limitations of this dataset for understanding the Heated Rivalry fandom?

- Difficulty: `hard`
- Answer type: `synthesis`
- Requires human review: `True`
- Support level: `supported`

### Agent Answer

The main limitations are search-result coverage, possible unrelated matches, point-in-time view/like/comment counts, missing comment text and transcripts, broad categories, and incomplete creator-supplied tags.

### SQL

No SQL used.

### Rows

```json
[]
```

### Self-Check

Supported by the documented gotchas rather than a single metric query.

### Limitations

- This is a methodological answer, not a new measurement from SQL.

### Expected Limitation

The answer should mention search-result coverage, missing comments/transcripts, point-in-time metrics, broad categories, and incomplete tags.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes:
- Follow-up artifact updates:
