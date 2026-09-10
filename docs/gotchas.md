# Gotchas

Known limitations and interpretation traps for the YouTube fandom dataset.

## Data Coverage

- The dataset comes from YouTube search results for `heated rivalry`, not from a complete catalog of every relevant video.
- YouTube may return videos that use the phrase "heated rivalry" but are unrelated to the show, book, or fandom.
- The fetch can stop below the requested target count when YouTube stops returning additional pages.
- Duplicate videos can appear across search result pages; the loader keeps one row per `videoId`.

## Point-In-Time Metrics

- `viewCount`, `likeCount`, and `commentCount` are snapshots from fetch time.
- These metrics should not be described as current unless the data was just refetched.
- A high view count can reflect age, platform promotion, channel size, or broad relevance, not only fandom interest.
- A high average view count for a small group can be unstable. Always compare the average with the number of videos in that group.

## Comments

- The database has `commentCount`, but not comment text.
- The agent cannot answer what viewers said, how fans felt in comments, or comment sentiment from the current database.
- Comment count can support engagement-volume analysis, but not sentiment analysis.

## Tags

- Tags are creator-supplied YouTube metadata.
- Many videos have no tags.
- Tags are not exhaustive and may be used for search optimization rather than accurate content description.
- `fact_video_tags` has one row per video/tag pair, so joining it to `fact_videos` can duplicate video rows.

## Topics

- Topics come from YouTube topic category URLs embedded in each video response.
- There is no separate YouTube topic lookup table in this database.
- `dim_topics.topicTitle` is parsed from the topic URL, so it should be treated as a readable label, not as separately verified metadata.
- `fact_video_topics` has one row per video/topic pair, so joining it to `fact_videos` can duplicate video rows.

## Categories

- YouTube category is one-to-one with a video.
- Category labels are broad, such as `Entertainment`, `People & Blogs`, or `Comedy`.
- Category should not be treated as a precise fandom or content-type classification.
- Category ID and category title live directly on `fact_videos`; there is no `fact_video_categories` table.

## Video Type

- The database does not have a true video-type field.
- Questions about "kind" or "type" of video need clarification or proxy dimensions.
- Available proxies include `categoryTitle`, `topicTitle`, `tag`, `channel`.
- Proxy-based answers should say which proxy was used.
- Do not claim that a video is official, fan-made, a reaction, a recap, an edit, or a trailer unless that is inferred from available metadata and stated as an inference.

## Duration

- Raw YouTube duration is stored as ISO 8601 text in `duration`.
- Numeric duration lives in `durationSeconds`.
- If YouTube omits duration or the format cannot be parsed, `durationSeconds` can be null.
- Very long videos can skew average duration; compare average and median together.

## Aggregation Grain

- `fact_videos` is one row per video.
- `fact_video_tags` is one row per video/tag pair.
- `fact_video_topics` is one row per video/topic pair.
- Use `COUNT(DISTINCT fact_videos.videoId)` when counting videos after joining to tag or topic tables.
- Use plain `COUNT(*)` on tag/topic fact tables only when counting tag or topic occurrences.

## Unsupported Questions

The current database cannot directly answer questions about:

- Transcript content.
- Spoken dialogue.
- Thumbnail imagery.
- Comment text or sentiment.
- Viewer demographics.
- Watch time or retention.
- Subscriber counts.
- Whether a video is official, fan-made, reaction, recap, or unrelated unless inferred from metadata.
