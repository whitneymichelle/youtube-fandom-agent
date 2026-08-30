# Semantic Model

This file defines the analytics concepts the LLM agent should use when answering questions about the YouTube dataset.

The modeled tables are:

- `fact_videos`
- `dim_categories`
- `dim_topics`
- `fact_video_tags`
- `fact_video_topics`

Use `videos` and `youtube_categories` as source/staging tables only. Agent-facing analysis should prefer the modeled tables.

## Model Row Counts

Use these metrics when the question asks how many rows exist in a table/model.

| Model | Grain | Row count metric |
| --- | --- | --- |
| `fact_videos` | one row per video | `SELECT COUNT(*) FROM fact_videos` |
| `dim_categories` | one row per category used by this dataset | `SELECT COUNT(*) FROM dim_categories` |
| `dim_topics` | one row per topic used by this dataset | `SELECT COUNT(*) FROM dim_topics` |
| `fact_video_tags` | one row per video/tag pair | `SELECT COUNT(*) FROM fact_video_tags` |
| `fact_video_topics` | one row per video/topic pair | `SELECT COUNT(*) FROM fact_video_topics` |

## Entities

### Videos

Table: `fact_videos`

Grain: one row per unique YouTube video.

Primary key: `videoId`

Dimensions:

| Dimension | Column | Type |
| --- | --- | --- |
| Video ID | `videoId` | `TEXT` |
| Title | `title` | `TEXT` |
| Description | `description` | `TEXT` |
| Channel | `channel` | `TEXT` |
| Published timestamp | `publishedAt` | `TEXT` |
| Duration | `duration` | `TEXT` |
| Duration seconds | `durationSeconds` | `INTEGER` |
| Category ID | `categoryId` | `TEXT` |
| Category | `categoryTitle` | `TEXT` |

Measures:

| Metric | SQL expression |
| --- | --- |
| Video count | `COUNT(*)` |
| Average views | `AVG(viewCount)` |
| Median views | median of `viewCount` |
| Min views | `MIN(viewCount)` |
| Max views | `MAX(viewCount)` |
| Average likes | `AVG(likeCount)` |
| Median likes | median of `likeCount` |
| Min likes | `MIN(likeCount)` |
| Max likes | `MAX(likeCount)` |
| Average comments | `AVG(commentCount)` |
| Median comments | median of `commentCount` |
| Min comments | `MIN(commentCount)` |
| Max comments | `MAX(commentCount)` |
| Average duration seconds | `AVG(durationSeconds)` |
| Median duration seconds | median of `durationSeconds` |
| Min duration seconds | `MIN(durationSeconds)` |
| Max duration seconds | `MAX(durationSeconds)` |

## Relationships

### Video Tags

Table: `fact_video_tags`

Grain: one row per video/tag pair.

Join:

```sql
fact_videos.videoId = fact_video_tags.videoId
```

Use this table for tag filtering, tag counts, and tag-level breakdowns.

Common metrics:

| Metric | SQL expression |
| --- | --- |
| Tagged video count | `COUNT(DISTINCT videoId)` |
| Tag occurrence count | `COUNT(*)` |
| Average tags per video | `COUNT(*) * 1.0 / COUNT(DISTINCT videoId)` |

### Video Topics

Table: `fact_video_topics`

Grain: one row per video/topic pair.

Join:

```sql
fact_videos.videoId = fact_video_topics.videoId
fact_video_topics.topicId = dim_topics.topicId
```

Use this table for topic filtering and topic-level breakdowns.

Common metrics:

| Metric | SQL expression |
| --- | --- |
| Topic video count | `COUNT(DISTINCT videoId)` |
| Topic occurrence count | `COUNT(*)` |

### Categories

Category is one-to-one with video in this dataset. Use `fact_videos.categoryTitle` for most category analysis.

Optional join:

```sql
fact_videos.categoryId = dim_categories.categoryId
```

Use `dim_categories` when a query asks specifically about the category dimension table.

## Median Pattern

SQLite does not have a built-in median aggregate. Use this window-function pattern, replacing `metric_column` and `base_query` as needed:

```sql
WITH ordered AS (
    SELECT
        metric_column,
        ROW_NUMBER() OVER (ORDER BY metric_column) AS row_num,
        COUNT(*) OVER () AS row_count
    FROM base_query
    WHERE metric_column IS NOT NULL
)
SELECT AVG(metric_column) AS median_metric
FROM ordered
WHERE row_num IN ((row_count + 1) / 2, (row_count + 2) / 2);
```

## Example Queries

### Overall Video Metrics

```sql
SELECT
    COUNT(*) AS video_count,
    AVG(viewCount) AS avg_views,
    MIN(viewCount) AS min_views,
    MAX(viewCount) AS max_views,
    AVG(likeCount) AS avg_likes,
    AVG(commentCount) AS avg_comments,
    AVG(durationSeconds) AS avg_duration_seconds
FROM fact_videos;
```

### Category Breakdown

```sql
SELECT
    categoryTitle,
    COUNT(*) AS video_count,
    AVG(viewCount) AS avg_views,
    AVG(likeCount) AS avg_likes,
    AVG(commentCount) AS avg_comments,
    AVG(durationSeconds) AS avg_duration_seconds
FROM fact_videos
GROUP BY categoryTitle
ORDER BY video_count DESC;
```

### Topic Breakdown

```sql
SELECT
    fvt.topicTitle,
    COUNT(DISTINCT fv.videoId) AS video_count,
    AVG(fv.viewCount) AS avg_views,
    AVG(fv.likeCount) AS avg_likes,
    AVG(fv.commentCount) AS avg_comments,
    AVG(fv.durationSeconds) AS avg_duration_seconds
FROM fact_videos fv
JOIN fact_video_topics fvt ON fvt.videoId = fv.videoId
GROUP BY fvt.topicId, fvt.topicTitle
ORDER BY video_count DESC;
```

### Tag Breakdown

```sql
SELECT
    ftag.tag,
    COUNT(DISTINCT fv.videoId) AS video_count,
    AVG(fv.viewCount) AS avg_views,
    AVG(fv.likeCount) AS avg_likes,
    AVG(fv.commentCount) AS avg_comments,
    AVG(fv.durationSeconds) AS avg_duration_seconds
FROM fact_videos fv
JOIN fact_video_tags ftag ON ftag.videoId = fv.videoId
GROUP BY ftag.tag
ORDER BY video_count DESC;
```
