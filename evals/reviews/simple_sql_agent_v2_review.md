# Simple SQL Agent V1 Review

Source results: `evals/results/simple_sql_agent_v1.jsonl`

## Summary

- Total eval questions: `30`
- Review items in this file: `11`
- Human review needed: `11`
- Answered with SQL: `22`
- Answered without SQL: `8`

Support levels:
- `partially_supported`: `1`
- `supported`: `23`
- `unsupported`: `6`

Review item difficulty:
- `hard`: `8`
- `medium`: `3`

Review item answer types:
- `answerability`: `3`
- `comparison`: `1`
- `grouped`: `2`
- `limitation`: `1`
- `synthesis`: `4`

Review question IDs: `q016, q018, q020, q021, q022, q023, q024, q025, q026, q027, q030`

## Review Instructions

Score each answer after reading the question, answer, SQL, self-check, and limitations.

Scoring:

- Correctness: `0` wrong/unsupported, `1` partially correct, `2` correct but thin, `3` correct and well-supported
- Groundedness: `0` not grounded, `1` weakly grounded, `2` mostly grounded, `3` properly grounded in schema/results
- Self-awareness: `0` overconfident/wrong, `1` vague, `2` mostly aware but incomplete, `3` accurately states support or limits

When feedback reveals a recurring failure, update the relevant system artifact: `docs/schema.md`, `docs/semantic_model.md`, `docs/gotchas.md`, `docs/agent_rules.md`, eval questions, examples, agent code, or tests.

## q016: Which tags are associated with the highest average view count?

- Difficulty: `medium`
- Answer type: `grouped`
- Requires human review: `True`
- Support level: `supported`

### Agent Answer

Top tags by average views: A$AP Rocky (6,640,333.00), ASAP Rocky (6,640,333.00), Finn Wolfhard (6,640,333.00), Finn Wolfhard hosts SNL (6,640,333.00), Finn Wolfhard interview (6,640,333.00).

### SQL

```sql
SELECT
                fvt.tag,
                COUNT(DISTINCT fv.videoId) AS video_count,
                AVG(fv.viewCount) AS avg_views,
                MIN(fv.viewCount) AS min_views,
                MAX(fv.viewCount) AS max_views
            FROM fact_video_tags AS fvt
            JOIN fact_videos AS fv
                ON fv.videoId = fvt.videoId
            GROUP BY fvt.tag
            ORDER BY avg_views DESC, video_count DESC, fvt.tag
            LIMIT 10
```

### Rows

```json
[
  {
    "tag": "A$AP Rocky",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "ASAP Rocky",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Finn Wolfhard",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Finn Wolfhard hosts SNL",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Finn Wolfhard interview",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Finn Wolfhard on SNL",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Ghostbusters: Afterlife",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "Hell of a Summer",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "It",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "tag": "It Chapter Two",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  }
]
```

### Self-Check

Supported by joining videos to tags and grouping by tag.

### Limitations

- Tags are creator-supplied and many videos have no tags.
- Small tag groups can have unstable averages.

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
- Support level: `supported`

### Agent Answer

Top channels by average views: Jeenie.Weenie (15,374,064.00), Saturday Night Live (6,640,333.00), BuzzFeed Celeb (5,885,290.00), Teen Vogue (3,781,372.00), Getaway Tiger (2,884,688.00).

### SQL

```sql
SELECT
                channel,
                COUNT(*) AS video_count,
                AVG(viewCount) AS avg_views,
                MIN(viewCount) AS min_views,
                MAX(viewCount) AS max_views
            FROM fact_videos
            GROUP BY channel
            ORDER BY avg_views DESC, video_count DESC, channel
            LIMIT 10
```

### Rows

```json
[
  {
    "channel": "Jeenie.Weenie",
    "video_count": 1,
    "avg_views": 15374064.0,
    "min_views": 15374064,
    "max_views": 15374064
  },
  {
    "channel": "Saturday Night Live",
    "video_count": 1,
    "avg_views": 6640333.0,
    "min_views": 6640333,
    "max_views": 6640333
  },
  {
    "channel": "BuzzFeed Celeb",
    "video_count": 1,
    "avg_views": 5885290.0,
    "min_views": 5885290,
    "max_views": 5885290
  },
  {
    "channel": "Teen Vogue",
    "video_count": 1,
    "avg_views": 3781372.0,
    "min_views": 3781372,
    "max_views": 3781372
  },
  {
    "channel": "Getaway Tiger",
    "video_count": 1,
    "avg_views": 2884688.0,
    "min_views": 2884688,
    "max_views": 2884688
  },
  {
    "channel": "Quinn",
    "video_count": 1,
    "avg_views": 2242547.0,
    "min_views": 2242547,
    "max_views": 2242547
  },
  {
    "channel": "Cosmopolitan",
    "video_count": 2,
    "avg_views": 2204744.5,
    "min_views": 1864411,
    "max_views": 2545078
  },
  {
    "channel": "Crave",
    "video_count": 29,
    "avg_views": 1980765.5862068965,
    "min_views": 102572,
    "max_views": 6241497
  },
  {
    "channel": "HBO Max",
    "video_count": 3,
    "avg_views": 1688221.3333333333,
    "min_views": 814364,
    "max_views": 3346589
  },
  {
    "channel": "Late Night with Seth Meyers",
    "video_count": 1,
    "avg_views": 1650254.0,
    "min_views": 1650254,
    "max_views": 1650254
  }
]
```

### Self-Check

Supported by grouping `fact_videos` by channel.

### Limitations

- Small channels can have unstable averages.

### Human Review

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes: 
- Follow-up artifact updates: 

## q020: Do videos tagged with 'heated rivalry' have higher average views than videos without that tag?

- Difficulty: `medium`
- Answer type: `comparison`
- Requires human review: `True`
- Support level: `supported`

### Agent Answer

No. Videos tagged with 'heated rivalry' average 330,643.00 views; videos without that tag average 454,617.01 views.

### SQL

```sql
WITH video_tag_status AS (
                SELECT
                    fv.videoId,
                    fv.viewCount,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM fact_video_tags AS fvt
                            WHERE fvt.videoId = fv.videoId
                                AND LOWER(fvt.tag) = 'heated rivalry'
                        )
                        THEN 'tagged_heated_rivalry'
                        ELSE 'not_tagged_heated_rivalry'
                    END AS tag_status
                FROM fact_videos AS fv
            )
            SELECT
                tag_status,
                COUNT(*) AS video_count,
                AVG(viewCount) AS avg_views,
                MIN(viewCount) AS min_views,
                MAX(viewCount) AS max_views
            FROM video_tag_status
            GROUP BY tag_status
            ORDER BY tag_status
```

### Rows

```json
[
  {
    "tag_status": "not_tagged_heated_rivalry",
    "video_count": 299,
    "avg_views": 454617.0100334448,
    "min_views": 0,
    "max_views": 15374064
  },
  {
    "tag_status": "tagged_heated_rivalry",
    "video_count": 204,
    "avg_views": 330643.0,
    "min_views": 93,
    "max_views": 6640333
  }
]
```

### Self-Check

Supported by classifying each video once using an EXISTS check against `fact_video_tags`, then comparing average view counts.

### Limitations

- Tags are creator-supplied and may be incomplete.
- This compares a tag proxy, not true Heated Rivalry relevance.

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

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes: 
- Follow-up artifact updates: 

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

- Correctness: 3
- Groundedness: 3
- Self-awareness: 3
- Notes: 
- Follow-up artifact updates: 

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
