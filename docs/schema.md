# Database Schema

This project stores YouTube data in `data/processed/heated_rivalry.db`.

The database has two layers:

- Source/staging tables preserve loaded API-shaped data.
- Modeled tables reshape the data for analysis.

## Source/Staging Tables

### `videos`

Grain: one row per unique YouTube video.

Source: loaded from `data/raw/heated_rivalry_batch_*.json`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `videoId` | `TEXT` | Primary key | YouTube video ID. |
| `title` | `TEXT` |  | Video title. |
| `description` | `TEXT` |  | Video description. |
| `channel` | `TEXT` |  | Channel title from the YouTube API response. |
| `publishedAt` | `TEXT` |  | Publish timestamp from YouTube, stored as ISO-like text. |
| `viewCount` | `INTEGER` |  | View count at fetch time. |
| `likeCount` | `INTEGER` |  | Like count at fetch time. |
| `commentCount` | `INTEGER` |  | Comment count at fetch time. |
| `duration` | `TEXT` |  | ISO 8601 duration string, such as `PT1M36S`. May be null if YouTube omits it. |
| `tags` | `TEXT` |  | JSON-encoded array of video tags. |
| `categoryId` | `TEXT` |  | YouTube category ID. |
| `topicIds` | `TEXT` |  | JSON-encoded array of topic category URLs. |

### `youtube_categories`

Grain: one row per official YouTube category for the fetched region.

Source: YouTube `videoCategories().list(...)` API response.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `categoryId` | `TEXT` | Primary key | YouTube category ID. |
| `title` | `TEXT` |  | Official YouTube category title. |
| `assignable` | `INTEGER` |  | Boolean-like value, stored as `0` or `1`, indicating whether videos can be assigned to this category. |
| `channelId` | `TEXT` |  | YouTube channel ID associated with the category metadata, when returned. |

## Modeled Tables

### `fact_videos`

Grain: one row per unique YouTube video.

Built from: `videos`, with category text joined from `youtube_categories`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `videoId` | `TEXT` | Primary key | YouTube video ID. |
| `title` | `TEXT` |  | Video title. |
| `description` | `TEXT` |  | Video description. |
| `channel` | `TEXT` |  | Channel title. |
| `publishedAt` | `TEXT` |  | Publish timestamp from YouTube, stored as ISO-like text. |
| `viewCount` | `INTEGER` |  | View count at fetch time. |
| `likeCount` | `INTEGER` |  | Like count at fetch time. |
| `commentCount` | `INTEGER` |  | Comment count at fetch time. |
| `duration` | `TEXT` |  | ISO 8601 duration string. |
| `durationSeconds` | `INTEGER` |  | Video duration converted to seconds for numeric aggregations. |
| `categoryId` | `TEXT` | Foreign key to `dim_categories.categoryId` | YouTube category ID. |
| `categoryTitle` | `TEXT` |  | Human-readable YouTube category title, denormalized onto the video fact because category is one-to-one with video. |

### `dim_categories`

Grain: one row per category used by the current video dataset.

Built from: distinct `videos.categoryId` values joined to `youtube_categories`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `categoryId` | `TEXT` | Primary key | YouTube category ID. |
| `categoryTitle` | `TEXT` |  | Human-readable YouTube category title. |

### `dim_topics`

Grain: one row per topic found in the current video dataset.

Built from: flattened `videos.topicIds`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `topicId` | `TEXT` | Primary key | Topic category URL from YouTube, usually a Wikipedia URL. |
| `topicTitle` | `TEXT` |  | Human-readable topic title parsed from `topicId`, such as `Ice hockey`. |

### `fact_video_tags`

Grain: one row per video/tag pair.

Built from: flattened `videos.tags`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `videoId` | `TEXT` | Composite primary key, foreign key to `fact_videos.videoId` | YouTube video ID. |
| `tag` | `TEXT` | Composite primary key | Individual YouTube video tag. |

### `fact_video_topics`

Grain: one row per video/topic pair.

Built from: flattened `videos.topicIds`.

| Column | Type | Key | Description |
| --- | --- | --- | --- |
| `videoId` | `TEXT` | Composite primary key, foreign key to `fact_videos.videoId` | YouTube video ID. |
| `topicId` | `TEXT` | Composite primary key, foreign key to `dim_topics.topicId` | Topic category URL from YouTube. |
| `topicTitle` | `TEXT` |  | Human-readable topic title denormalized for easier querying. |

## Relationships

```text
videos
  -> fact_videos
  -> fact_video_tags
  -> fact_video_topics
  -> dim_topics

youtube_categories
  -> dim_categories
  -> fact_videos.categoryId / fact_videos.categoryTitle
```

`fact_video_categories` does not exist because each YouTube video has only one category. Category ID and title live directly on `fact_videos`.
