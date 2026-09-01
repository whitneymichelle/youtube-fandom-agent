"""
Deterministic SQL-backed baseline agent.

This first agent intentionally avoids LLM calls. It gives the project a
measurable baseline for exact and simple grouped questions before adding
free-form SQL generation or RAG.
"""

from dataclasses import dataclass
import argparse
import re
import sqlite3
from typing import Any, Callable, Dict, List, Optional, Sequence


@dataclass
class AgentAnswer:
    """Structured answer returned by the simple SQL agent."""

    question: str
    answer: str
    sql: Optional[str]
    rows: List[Dict[str, Any]]
    support_level: str
    self_check: str
    limitations: List[str]


class SimpleSQLAgent:
    """Answer simple metric questions from the modeled SQLite tables."""

    def __init__(self, db_path: str = "data/processed/heated_rivalry.db"):
        self.db_path = db_path
        self.handlers: Sequence[Callable[[str], Optional[AgentAnswer]]] = (
            self._video_count,
            self._modeled_table_counts,
            self._average_views,
            self._median_views,
            self._min_max_views,
            self._like_summary,
            self._comment_summary,
            self._duration_summary,
            self._most_viewed_video,
            self._distinct_categories_and_topics,
            self._top_categories_by_count,
            self._top_categories_by_avg_views,
            self._top_topics_by_count,
            self._top_topics_by_avg_views,
            self._top_tags_by_count,
            self._top_channels_by_count,
            self._entertainment_vs_people_blogs_avg_views,
            self._tagged_video_coverage,
            self._average_tags_per_tagged_video,
            self._comments_answerability,
            self._sentiment_answerability,
            self._content_type_answerability,
            self._dataset_limitations,
        )

    def answer(self, question: str) -> AgentAnswer:
        """Answer a question if it matches a supported V1 pattern."""
        normalized = self._normalize(question)
        for handler in self.handlers:
            response = handler(normalized)
            if response:
                response.question = question
                return response

        return AgentAnswer(
            question=question,
            answer=(
                "I do not have a supported query pattern for that question yet."
            ),
            sql=None,
            rows=[],
            support_level="unsupported",
            self_check=(
                "Unsupported by this V1 deterministic agent. Add a new handler "
                "or use a later LLM SQL-generation pass."
            ),
            limitations=[
                "This baseline only answers predefined SQL and answerability patterns."
            ],
        )

    def _execute(self, sql: str) -> List[Dict[str, Any]]:
        self._validate_select(sql)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]

    def _make_answer(
        self,
        *,
        question: str = "",
        answer: str,
        sql: Optional[str],
        rows: Optional[List[Dict[str, Any]]] = None,
        support_level: str = "supported",
        self_check: str,
        limitations: Optional[List[str]] = None,
    ) -> AgentAnswer:
        return AgentAnswer(
            question=question,
            answer=answer,
            sql=sql,
            rows=rows or [],
            support_level=support_level,
            self_check=self_check,
            limitations=limitations or [],
        )

    @staticmethod
    def _normalize(question: str) -> str:
        return re.sub(r"\s+", " ", question.lower().strip())

    @staticmethod
    def _validate_select(sql: str) -> None:
        cleaned = sql.strip().lower()
        if not cleaned.startswith(("select", "with")):
            raise ValueError("Only read-only SELECT queries are allowed.")
        if re.search(r"\b(insert|update|delete|drop|alter|create|replace)\b", cleaned):
            raise ValueError("Only read-only SELECT queries are allowed.")

    @staticmethod
    def _format_int(value: Any) -> str:
        return f"{int(value):,}"

    @staticmethod
    def _format_float(value: Any, decimals: int = 2) -> str:
        return f"{float(value):,.{decimals}f}"

    @staticmethod
    def _metric_summary_sql(metric_column: str) -> str:
        return f"""
            WITH ordered AS (
                SELECT
                    {metric_column} AS value,
                    ROW_NUMBER() OVER (ORDER BY {metric_column}) AS row_num,
                    COUNT(*) OVER () AS row_count
                FROM fact_videos
                WHERE {metric_column} IS NOT NULL
            )
            SELECT
                COUNT(*) AS count_values,
                AVG(value) AS avg_value,
                AVG(CASE
                    WHEN row_num IN ((row_count + 1) / 2, (row_count + 2) / 2)
                    THEN value
                END) AS median_value,
                MIN(value) AS min_value,
                MAX(value) AS max_value
            FROM ordered
        """

    def _video_count(self, question: str) -> Optional[AgentAnswer]:
        if not re.search(r"\bhow many videos\b", question):
            return None
        sql = "SELECT COUNT(*) AS video_count FROM fact_videos"
        rows = self._execute(sql)
        return self._make_answer(
            answer=f"The dataset has {self._format_int(rows[0]['video_count'])} videos.",
            sql=sql,
            rows=rows,
            self_check="Supported directly by `COUNT(*)` at the `fact_videos` grain.",
        )

    def _modeled_table_counts(self, question: str) -> Optional[AgentAnswer]:
        if "rows are in each modeled table" not in question:
            return None
        sql = """
            SELECT 'fact_videos' AS model, COUNT(*) AS row_count FROM fact_videos
            UNION ALL
            SELECT 'dim_categories', COUNT(*) FROM dim_categories
            UNION ALL
            SELECT 'dim_topics', COUNT(*) FROM dim_topics
            UNION ALL
            SELECT 'fact_video_tags', COUNT(*) FROM fact_video_tags
            UNION ALL
            SELECT 'fact_video_topics', COUNT(*) FROM fact_video_topics
            ORDER BY model
        """
        rows = self._execute(sql)
        counts = ", ".join(
            f"{row['model']}: {self._format_int(row['row_count'])}" for row in rows
        )
        return self._make_answer(
            answer=f"Modeled table row counts are {counts}.",
            sql=sql,
            rows=rows,
            self_check="Supported directly by row counts over each modeled table.",
        )

    def _average_views(self, question: str) -> Optional[AgentAnswer]:
        if "average view count across all videos" not in question:
            return None
        sql = "SELECT AVG(viewCount) AS avg_views FROM fact_videos"
        rows = self._execute(sql)
        return self._make_answer(
            answer=(
                "The average view count is "
                f"{self._format_float(rows[0]['avg_views'])} views."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported directly by `AVG(viewCount)` at the video grain.",
            limitations=["View counts are point-in-time snapshots from fetch time."],
        )

    def _median_views(self, question: str) -> Optional[AgentAnswer]:
        if "median view count" not in question:
            return None
        return self._summary_metric_answer(
            question,
            "viewCount",
            "view count",
            only_median=True,
        )

    def _min_max_views(self, question: str) -> Optional[AgentAnswer]:
        if "min and max view" not in question:
            return None
        sql = "SELECT MIN(viewCount) AS min_views, MAX(viewCount) AS max_views FROM fact_videos"
        rows = self._execute(sql)
        return self._make_answer(
            answer=(
                f"View counts range from {self._format_int(rows[0]['min_views'])} "
                f"to {self._format_int(rows[0]['max_views'])}."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported directly by min/max over `fact_videos.viewCount`.",
        )

    def _like_summary(self, question: str) -> Optional[AgentAnswer]:
        if "like count" not in question:
            return None
        return self._summary_metric_answer(question, "likeCount", "like count")

    def _comment_summary(self, question: str) -> Optional[AgentAnswer]:
        if "comment count" not in question or question.startswith("can "):
            return None
        return self._summary_metric_answer(question, "commentCount", "comment count")

    def _duration_summary(self, question: str) -> Optional[AgentAnswer]:
        if "duration" not in question or "seconds" not in question:
            return None
        return self._summary_metric_answer(
            question,
            "durationSeconds",
            "duration in seconds",
        )

    def _summary_metric_answer(
        self,
        question: str,
        metric_column: str,
        label: str,
        only_median: bool = False,
    ) -> AgentAnswer:
        sql = self._metric_summary_sql(metric_column)
        rows = self._execute(sql)
        row = rows[0]
        if only_median:
            answer = (
                f"The median {label} is "
                f"{self._format_float(row['median_value'], decimals=1)}."
            )
        else:
            answer = (
                f"For {label}: average {self._format_float(row['avg_value'])}, "
                f"median {self._format_float(row['median_value'], decimals=1)}, "
                f"min {self._format_int(row['min_value'])}, "
                f"max {self._format_int(row['max_value'])}."
            )
        return self._make_answer(
            answer=answer,
            sql=sql,
            rows=rows,
            self_check=(
                f"Supported by aggregating `{metric_column}` at the "
                "`fact_videos` grain and excluding null values."
            ),
            limitations=["Averages can be skewed by outliers; compare to median."],
        )

    def _most_viewed_video(self, question: str) -> Optional[AgentAnswer]:
        if "video has the most views" not in question:
            return None
        sql = """
            SELECT videoId, title, channel, viewCount
            FROM fact_videos
            ORDER BY viewCount DESC
            LIMIT 1
        """
        rows = self._execute(sql)
        row = rows[0]
        return self._make_answer(
            answer=(
                f"The most-viewed video is \"{row['title']}\" by {row['channel']} "
                f"with {self._format_int(row['viewCount'])} views."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported by sorting videos by `viewCount` descending.",
            limitations=["View counts are point-in-time snapshots from fetch time."],
        )

    def _distinct_categories_and_topics(self, question: str) -> Optional[AgentAnswer]:
        if "distinct categories and topics" not in question:
            return None
        sql = """
            SELECT 'categories' AS dimension, COUNT(*) AS count FROM dim_categories
            UNION ALL
            SELECT 'topics', COUNT(*) FROM dim_topics
        """
        rows = self._execute(sql)
        counts = {row["dimension"]: row["count"] for row in rows}
        return self._make_answer(
            answer=(
                f"The dataset has {counts['categories']} distinct categories and "
                f"{counts['topics']} distinct topics."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported directly by row counts in the dimension tables.",
        )

    def _top_categories_by_count(self, question: str) -> Optional[AgentAnswer]:
        if "categories have the most videos" not in question:
            return None
        sql = """
            SELECT categoryTitle, COUNT(*) AS video_count
            FROM fact_videos
            GROUP BY categoryTitle
            ORDER BY video_count DESC
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top categories by video count",
            "categoryTitle",
            "video_count",
            "Supported by grouping `fact_videos` at the category grain.",
        )

    def _top_categories_by_avg_views(self, question: str) -> Optional[AgentAnswer]:
        if "categories have the highest average view count" not in question:
            return None
        sql = """
            SELECT categoryTitle, COUNT(*) AS video_count, AVG(viewCount) AS avg_views
            FROM fact_videos
            GROUP BY categoryTitle
            ORDER BY avg_views DESC
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top categories by average views",
            "categoryTitle",
            "avg_views",
            "Supported by grouping `fact_videos` by category.",
            limitations=["Small categories can have unstable averages."],
        )

    def _top_topics_by_count(self, question: str) -> Optional[AgentAnswer]:
        if "topics appear on the most videos" not in question:
            return None
        sql = """
            SELECT topicTitle, COUNT(DISTINCT videoId) AS video_count
            FROM fact_video_topics
            GROUP BY topicId, topicTitle
            ORDER BY video_count DESC
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top topics by video count",
            "topicTitle",
            "video_count",
            "Supported by counting distinct videos at the video/topic grain.",
        )

    def _top_topics_by_avg_views(self, question: str) -> Optional[AgentAnswer]:
        if "topics have the highest average view count" not in question:
            return None
        sql = """
            SELECT
                fvt.topicTitle,
                COUNT(DISTINCT fv.videoId) AS video_count,
                AVG(fv.viewCount) AS avg_views
            FROM fact_videos fv
            JOIN fact_video_topics fvt ON fvt.videoId = fv.videoId
            GROUP BY fvt.topicId, fvt.topicTitle
            ORDER BY avg_views DESC
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top topics by average views",
            "topicTitle",
            "avg_views",
            "Supported by joining videos to topics and grouping by topic.",
            limitations=["Topic joins are one-to-many, so video counts use distinct IDs."],
        )

    def _top_tags_by_count(self, question: str) -> Optional[AgentAnswer]:
        if "tags appear most often" not in question:
            return None
        sql = """
            SELECT tag, COUNT(*) AS tag_occurrences
            FROM fact_video_tags
            GROUP BY tag
            ORDER BY tag_occurrences DESC, tag
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top tags by occurrence count",
            "tag",
            "tag_occurrences",
            "Supported by counting rows at the video/tag grain.",
            limitations=["Tags are creator-supplied and many videos have no tags."],
        )

    def _top_channels_by_count(self, question: str) -> Optional[AgentAnswer]:
        if "channels have the most videos" not in question:
            return None
        sql = """
            SELECT channel, COUNT(*) AS video_count
            FROM fact_videos
            GROUP BY channel
            ORDER BY video_count DESC, channel
            LIMIT 10
        """
        return self._top_list_answer(
            sql,
            "Top channels by video count",
            "channel",
            "video_count",
            "Supported by grouping `fact_videos` by channel.",
        )

    def _top_list_answer(
        self,
        sql: str,
        prefix: str,
        label_column: str,
        metric_column: str,
        self_check: str,
        limitations: Optional[List[str]] = None,
    ) -> AgentAnswer:
        rows = self._execute(sql)
        parts = []
        for row in rows[:5]:
            value = row[metric_column]
            if isinstance(value, float):
                formatted = self._format_float(value)
            else:
                formatted = self._format_int(value)
            parts.append(f"{row[label_column]} ({formatted})")
        return self._make_answer(
            answer=f"{prefix}: " + ", ".join(parts) + ".",
            sql=sql,
            rows=rows,
            self_check=self_check,
            limitations=limitations,
        )

    def _entertainment_vs_people_blogs_avg_views(
        self,
        question: str,
    ) -> Optional[AgentAnswer]:
        if "entertainment videos" not in question or "people & blogs" not in question:
            return None
        sql = """
            SELECT categoryTitle, COUNT(*) AS video_count, AVG(viewCount) AS avg_views
            FROM fact_videos
            WHERE categoryTitle IN ('Entertainment', 'People & Blogs')
            GROUP BY categoryTitle
            ORDER BY categoryTitle
        """
        rows = self._execute(sql)
        values = {row["categoryTitle"]: row["avg_views"] for row in rows}
        if values.get("Entertainment", 0) > values.get("People & Blogs", 0):
            verdict = "Yes"
        else:
            verdict = "No"
        return self._make_answer(
            answer=(
                f"{verdict}. Entertainment averages "
                f"{self._format_float(values.get('Entertainment', 0))} views; "
                f"People & Blogs averages "
                f"{self._format_float(values.get('People & Blogs', 0))} views."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported by filtering and grouping videos by category.",
            limitations=["Category labels are broad and not fandom-specific."],
        )

    def _tagged_video_coverage(self, question: str) -> Optional[AgentAnswer]:
        if "dataset has creator-supplied tags" not in question:
            return None
        sql = """
            WITH tagged AS (
                SELECT COUNT(DISTINCT videoId) AS tagged_videos
                FROM fact_video_tags
            ),
            total AS (
                SELECT COUNT(*) AS total_videos
                FROM fact_videos
            )
            SELECT
                tagged_videos,
                total_videos,
                tagged_videos * 100.0 / total_videos AS tagged_percent
            FROM tagged, total
        """
        rows = self._execute(sql)
        row = rows[0]
        return self._make_answer(
            answer=(
                f"{self._format_int(row['tagged_videos'])} of "
                f"{self._format_int(row['total_videos'])} videos have tags "
                f"({self._format_float(row['tagged_percent'])}%)."
            ),
            sql=sql,
            rows=rows,
            self_check=(
                "Supported by counting distinct tagged videos and dividing by "
                "the `fact_videos` row count."
            ),
            limitations=["Tags are creator-supplied and may be incomplete."],
        )

    def _average_tags_per_tagged_video(self, question: str) -> Optional[AgentAnswer]:
        if "tags does a tagged video have on average" not in question:
            return None
        sql = """
            SELECT COUNT(*) * 1.0 / COUNT(DISTINCT videoId) AS avg_tags
            FROM fact_video_tags
        """
        rows = self._execute(sql)
        return self._make_answer(
            answer=(
                "Tagged videos have "
                f"{self._format_float(rows[0]['avg_tags'])} tags on average."
            ),
            sql=sql,
            rows=rows,
            self_check="Supported by the video/tag table grain.",
            limitations=["This excludes videos with zero tags."],
        )

    def _comments_answerability(self, question: str) -> Optional[AgentAnswer]:
        if "what fans are saying in the comments" not in question:
            return None
        return self._make_answer(
            answer=(
                "No. The database has `commentCount`, but it does not contain "
                "comment text, so it cannot answer what fans are saying."
            ),
            sql=None,
            support_level="unsupported",
            self_check="Correctly unsupported: comment content is not in the schema.",
            limitations=["Only comment counts are available."],
        )

    def _sentiment_answerability(self, question: str) -> Optional[AgentAnswer]:
        if "infer fan sentiment from comment counts" not in question:
            return None
        return self._make_answer(
            answer=(
                "No. Comment counts measure engagement volume, not whether the "
                "comments are positive, negative, or mixed."
            ),
            sql=None,
            support_level="unsupported",
            self_check="Correctly unsupported: sentiment needs comment text or labels.",
            limitations=["The database does not include comment text or sentiment labels."],
        )

    def _content_type_answerability(self, question: str) -> Optional[AgentAnswer]:
        if "reaction, recap, edit, trailer, or official clip" not in question:
            return None
        return self._make_answer(
            answer=(
                "Only partially. The database has title, description, channel, "
                "tags, categories, and topics, but no explicit content-type label."
            ),
            sql=None,
            support_level="partially_supported",
            self_check=(
                "Partially supported: the answer would require heuristic labels "
                "from metadata."
            ),
            limitations=[
                "No explicit official/fan/reaction/recap/edit/trailer label exists."
            ],
        )

    def _dataset_limitations(self, question: str) -> Optional[AgentAnswer]:
        if "main limitations" not in question:
            return None
        return self._make_answer(
            answer=(
                "The main limitations are search-result coverage, possible unrelated "
                "matches, point-in-time view/like/comment counts, missing comment text "
                "and transcripts, broad categories, and incomplete creator-supplied tags."
            ),
            sql=None,
            support_level="supported",
            self_check=(
                "Supported by the documented gotchas rather than a single metric query."
            ),
            limitations=[
                "This is a methodological answer, not a new measurement from SQL."
            ],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the simple YouTube SQL agent.")
    parser.add_argument("question", help="Question to answer from the modeled DB")
    parser.add_argument(
        "--db",
        default="data/processed/heated_rivalry.db",
        help="Path to SQLite database",
    )
    args = parser.parse_args()

    response = SimpleSQLAgent(args.db).answer(args.question)
    print(f"Answer: {response.answer}")
    if response.sql:
        print("\nSQL:")
        print(response.sql.strip())
    print(f"\nSupport: {response.support_level}")
    print(f"Self-check: {response.self_check}")
    if response.limitations:
        print("\nLimitations:")
        for limitation in response.limitations:
            print(f"- {limitation}")


if __name__ == "__main__":
    main()
