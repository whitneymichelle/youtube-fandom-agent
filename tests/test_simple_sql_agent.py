import json

from src.agents.simple_sql_agent import SimpleSQLAgent
from src.youtube_api.loader import YouTubeDataLoader


def write_batch(raw_dir, batch_num, videos):
    raw_dir.mkdir(parents=True, exist_ok=True)
    batch_file = raw_dir / f"heated_rivalry_batch_{batch_num}.json"
    batch_file.write_text(json.dumps(videos), encoding="utf-8")


def make_video(
    video_id,
    title,
    channel,
    views,
    likes,
    comments,
    duration,
    category_id,
    tags=None,
    topic_ids=None,
):
    return {
        "videoId": video_id,
        "title": title,
        "description": "A test video",
        "channel": channel,
        "publishedAt": "2026-08-29T00:00:00Z",
        "viewCount": views,
        "likeCount": likes,
        "commentCount": comments,
        "duration": duration,
        "tags": json.dumps(tags or []),
        "categoryId": category_id,
        "topicIds": json.dumps(topic_ids or []),
    }


def create_agent_db(tmp_path):
    raw_dir = tmp_path / "raw"
    db_path = tmp_path / "heated_rivalry.db"

    write_batch(
        raw_dir,
        1,
        [
            make_video(
                "video-1",
                "Official trailer",
                "Crave",
                100,
                10,
                1,
                "PT1M",
                "24",
                tags=["heated rivalry", "trailer"],
                topic_ids=["https://en.wikipedia.org/wiki/Television_program"],
            ),
            make_video(
                "video-2",
                "Fan edit",
                "Fan Channel",
                300,
                30,
                3,
                "PT2M",
                "22",
                tags=["heated rivalry", "fanedit"],
                topic_ids=["https://en.wikipedia.org/wiki/Entertainment"],
            ),
            make_video(
                "video-3",
                "Comedy sketch",
                "Sketch Channel",
                500,
                50,
                5,
                "PT3M",
                "23",
                tags=[],
                topic_ids=["https://en.wikipedia.org/wiki/Entertainment"],
            ),
        ],
    )

    loader = YouTubeDataLoader(str(db_path))
    try:
        loader.create_table()
        loader.load_from_json_files(str(raw_dir))
        loader.cursor.execute("""
            CREATE TABLE youtube_categories (
                categoryId TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                assignable INTEGER,
                channelId TEXT
            )
        """)
        loader.cursor.executemany(
            """
            INSERT INTO youtube_categories (categoryId, title, assignable, channelId)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("22", "People & Blogs", 1, "channel-22"),
                ("23", "Comedy", 1, "channel-23"),
                ("24", "Entertainment", 1, "channel-24"),
            ],
        )
        loader.conn.commit()
        loader.build_modeled_tables()
    finally:
        loader.close()

    return db_path


def test_agent_answers_video_count(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer("How many videos are in the dataset?")

    assert "3 videos" in response.answer
    assert response.support_level == "supported"
    assert "COUNT(*)" in response.sql


def test_agent_answers_average_views(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer("What is the average view count across all videos?")

    assert "300.00 views" in response.answer
    assert response.support_level == "supported"
    assert response.rows == [{"avg_views": 300.0}]


def test_agent_answers_top_categories(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer("Which categories have the most videos?")

    assert "Top categories by video count" in response.answer
    assert "Comedy (1)" in response.answer
    assert "Entertainment (1)" in response.answer
    assert "People & Blogs (1)" in response.answer


def test_agent_answers_topic_average_views_without_using_overall_average(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer("Which topics have the highest average view count?")

    assert "Top topics by average views" in response.answer
    assert response.rows[0]["topicTitle"] == "Entertainment"
    assert response.rows[0]["avg_views"] == 400.0


def test_agent_reports_comment_text_as_unsupported(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer("Can we tell what fans are saying in the comments?")

    assert response.support_level == "unsupported"
    assert response.sql is None
    assert "comment text" in response.answer


def test_agent_reports_content_type_as_partial(tmp_path):
    agent = SimpleSQLAgent(str(create_agent_db(tmp_path)))

    response = agent.answer(
        "Can we identify whether a video is a reaction, recap, edit, trailer, or official clip?"
    )

    assert response.support_level == "partially_supported"
    assert response.sql is None
    assert "no explicit content-type label" in response.answer
