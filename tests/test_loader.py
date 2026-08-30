import json

from src.youtube_api.loader import YouTubeDataLoader, parse_duration_seconds


def write_batch(raw_dir, batch_num, videos):
    raw_dir.mkdir(parents=True, exist_ok=True)
    batch_file = raw_dir / f"heated_rivalry_batch_{batch_num}.json"
    batch_file.write_text(json.dumps(videos), encoding="utf-8")
    return batch_file


def make_video(
    video_id,
    tags=None,
    topic_ids=None,
    category_id="24",
    title="Test Video",
    duration="PT1M",
):
    return {
        "videoId": video_id,
        "title": title,
        "description": "A test video",
        "channel": "Test Channel",
        "publishedAt": "2026-08-29T00:00:00Z",
        "viewCount": 100,
        "likeCount": 10,
        "commentCount": 2,
        "duration": duration,
        "tags": json.dumps(tags or []),
        "categoryId": category_id,
        "topicIds": json.dumps(topic_ids or []),
    }


def create_loader(tmp_path):
    db_path = tmp_path / "heated_rivalry.db"
    loader = YouTubeDataLoader(str(db_path))
    loader.create_table()
    return loader


def table_names(loader):
    rows = loader.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row[0] for row in rows}


def test_load_from_json_files_preserves_metadata(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(
        raw_dir,
        1,
        [
            make_video(
                "video-1",
                tags=["heated rivalry", "hockey"],
                topic_ids=["https://en.wikipedia.org/wiki/Ice_hockey"],
                category_id="24",
            )
        ],
    )

    loader = create_loader(tmp_path)
    try:
        stats = loader.load_from_json_files(str(raw_dir))

        row = loader.cursor.execute(
            """
            SELECT videoId, tags, categoryId, topicIds
            FROM videos
            WHERE videoId = ?
            """,
            ("video-1",),
        ).fetchone()

        assert stats == {
            "total_loaded": 1,
            "duplicates_skipped": 0,
            "batch_files": 1,
        }
        assert row == (
            "video-1",
            json.dumps(["heated rivalry", "hockey"]),
            "24",
            json.dumps(["https://en.wikipedia.org/wiki/Ice_hockey"]),
        )
    finally:
        loader.close()


def test_load_from_json_files_skips_duplicate_video_ids(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(raw_dir, 1, [make_video("duplicate-video")])
    write_batch(raw_dir, 2, [make_video("duplicate-video")])

    loader = create_loader(tmp_path)
    try:
        stats = loader.load_from_json_files(str(raw_dir))
        video_count = loader.cursor.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

        assert stats["total_loaded"] == 1
        assert stats["duplicates_skipped"] == 1
        assert video_count == 1
    finally:
        loader.close()


def test_build_modeled_tables_creates_expected_tables(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(raw_dir, 1, [make_video("video-1")])

    loader = create_loader(tmp_path)
    try:
        loader.load_from_json_files(str(raw_dir))
        loader.build_modeled_tables()

        assert {
            "fact_videos",
            "dim_categories",
            "dim_topics",
            "fact_video_tags",
            "fact_video_topics",
        }.issubset(table_names(loader))
        assert "fact_video_categories" not in table_names(loader)
    finally:
        loader.close()


def test_build_modeled_tables_flattens_tags(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(
        raw_dir,
        1,
        [make_video("video-1", tags=["heated rivalry", "hockey", "fanedit"])],
    )

    loader = create_loader(tmp_path)
    try:
        loader.load_from_json_files(str(raw_dir))
        loader.build_modeled_tables()

        rows = loader.cursor.execute(
            """
            SELECT tag
            FROM fact_video_tags
            WHERE videoId = ?
            ORDER BY tag
            """,
            ("video-1",),
        ).fetchall()

        assert [row[0] for row in rows] == ["fanedit", "heated rivalry", "hockey"]
    finally:
        loader.close()


def test_build_modeled_tables_flattens_topics(tmp_path):
    raw_dir = tmp_path / "raw"
    topic_id = "https://en.wikipedia.org/wiki/Ice_hockey"
    write_batch(raw_dir, 1, [make_video("video-1", topic_ids=[topic_id])])

    loader = create_loader(tmp_path)
    try:
        loader.load_from_json_files(str(raw_dir))
        loader.build_modeled_tables()

        topic = loader.cursor.execute(
            "SELECT topicTitle FROM dim_topics WHERE topicId = ?",
            (topic_id,),
        ).fetchone()
        link = loader.cursor.execute(
            """
            SELECT videoId, topicId, topicTitle
            FROM fact_video_topics
            WHERE videoId = ? AND topicId = ?
            """,
            ("video-1", topic_id),
        ).fetchone()

        assert topic == ("Ice hockey",)
        assert link == ("video-1", topic_id, "Ice hockey")
    finally:
        loader.close()


def test_build_modeled_tables_denormalizes_category_title_on_fact_videos(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(raw_dir, 1, [make_video("video-1", category_id="24")])

    loader = create_loader(tmp_path)
    try:
        loader.load_from_json_files(str(raw_dir))
        loader.cursor.execute("""
            CREATE TABLE youtube_categories (
                categoryId TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                assignable INTEGER,
                channelId TEXT
            )
        """)
        loader.cursor.execute(
            """
            INSERT INTO youtube_categories (categoryId, title, assignable, channelId)
            VALUES (?, ?, ?, ?)
            """,
            ("24", "Entertainment", 1, "channel-1"),
        )
        loader.conn.commit()

        loader.build_modeled_tables()

        category = loader.cursor.execute(
            """
            SELECT videoId, categoryId, categoryTitle
            FROM fact_videos
            WHERE videoId = ?
            """,
            ("video-1",),
        ).fetchone()

        assert category == ("video-1", "24", "Entertainment")
    finally:
        loader.close()


def test_parse_duration_seconds():
    assert parse_duration_seconds("PT16S") == 16
    assert parse_duration_seconds("PT1M36S") == 96
    assert parse_duration_seconds("PT1H2M3S") == 3723
    assert parse_duration_seconds("P1DT2H") == 93600
    assert parse_duration_seconds(None) is None
    assert parse_duration_seconds("not-a-duration") is None


def test_build_modeled_tables_adds_duration_seconds(tmp_path):
    raw_dir = tmp_path / "raw"
    write_batch(raw_dir, 1, [make_video("video-1", duration="PT1H2M3S")])

    loader = create_loader(tmp_path)
    try:
        loader.load_from_json_files(str(raw_dir))
        loader.build_modeled_tables()

        duration_seconds = loader.cursor.execute(
            "SELECT durationSeconds FROM fact_videos WHERE videoId = ?",
            ("video-1",),
        ).fetchone()

        assert duration_seconds == (3723,)
    finally:
        loader.close()
