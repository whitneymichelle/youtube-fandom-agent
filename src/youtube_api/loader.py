"""
Load raw YouTube JSON data into SQLite database.
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional


def parse_duration_seconds(duration: str) -> Optional[int]:
    """Convert a YouTube ISO 8601 duration string to seconds."""
    if not duration:
        return None

    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?"
        r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
        r"(?:(?P<seconds>\d+)S)?)?",
        duration,
    )
    if not match:
        return None

    parts = {key: int(value or 0) for key, value in match.groupdict().items()}
    return (
        parts["days"] * 86400
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )


class YouTubeDataLoader:
    """Load YouTube JSON files into SQLite database."""
    
    def __init__(self, db_path: str = "data/processed/heated_rivalry.db"):
        """
        Initialize the data loader.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def create_table(self):
        """Create videos table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                videoId TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                channel TEXT,
                publishedAt TEXT,
                viewCount INTEGER,
                likeCount INTEGER,
                commentCount INTEGER,
                duration TEXT,
                tags TEXT,
                categoryId TEXT,
                topicIds TEXT
            )
        """)
        self.conn.commit()
    
    def load_from_json_files(self, json_dir: str = "data/raw") -> Dict[str, Any]:
        """
        Load all JSON batch files and insert into database.
        
        Args:
            json_dir: Directory containing batch JSON files
            
        Returns:
            Dict with load statistics
        """
        json_files = sorted(Path(json_dir).glob("heated_rivalry_batch_*.json"))
        
        if not json_files:
            raise FileNotFoundError(f"No batch files found in {json_dir}")
        
        total_videos = 0
        duplicates_skipped = 0
        
        for json_file in json_files:
            with open(json_file) as f:
                videos = json.load(f)
            
            for video in videos:
                try:
                    self.cursor.execute("""
                        INSERT INTO videos (
                            videoId, title, description, channel,
                            publishedAt, viewCount, likeCount,
                            commentCount, duration, tags, categoryId, topicIds
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        video['videoId'],
                        video['title'],
                        video['description'],
                        video['channel'],
                        video['publishedAt'],
                        video['viewCount'],
                        video['likeCount'],
                        video['commentCount'],
                        video['duration'],
                        video.get('tags', '[]'),
                        video.get('categoryId', None),
                        video.get('topicIds', '[]')
                    ))
                    total_videos += 1
                except sqlite3.IntegrityError:
                    # videoId already exists (duplicate)
                    duplicates_skipped += 1
            
            self.conn.commit()
            print(f"✓ Loaded {json_file.name}: {len(videos)} videos")
        
        return {
            'total_loaded': total_videos,
            'duplicates_skipped': duplicates_skipped,
            'batch_files': len(json_files)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics from the loaded data."""
        self.cursor.execute("SELECT COUNT(*) FROM videos")
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT channel, COUNT(*) as count 
            FROM videos 
            GROUP BY channel 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_channels = self.cursor.fetchall()
        
        self.cursor.execute("""
            SELECT 
                AVG(viewCount) as avg_views,
                MAX(viewCount) as max_views,
                MIN(viewCount) as min_views
            FROM videos
        """)
        view_stats = self.cursor.fetchone()
        
        return {
            'total_videos': total,
            'top_channels': top_channels,
            'avg_views': int(view_stats[0]) if view_stats[0] else 0,
            'max_views': view_stats[1],
            'min_views': view_stats[2]
        }

    def build_modeled_tables(self) -> Dict[str, int]:
        """Build analytics-friendly fact and dimension tables from videos."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS youtube_categories (
                categoryId TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                assignable INTEGER,
                channelId TEXT
            );

            DROP TABLE IF EXISTS fact_video_categories;
            DROP TABLE IF EXISTS video_topics;
            DROP TABLE IF EXISTS youtube_topics;
            DROP TABLE IF EXISTS fact_video_topics;
            DROP TABLE IF EXISTS fact_video_tags;
            DROP TABLE IF EXISTS dim_categories;
            DROP TABLE IF EXISTS dim_topics;
            DROP TABLE IF EXISTS fact_videos;

            CREATE TABLE fact_videos (
                videoId TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                channel TEXT,
                publishedAt TEXT,
                viewCount INTEGER,
                likeCount INTEGER,
                commentCount INTEGER,
                duration TEXT,
                durationSeconds INTEGER,
                categoryId TEXT,
                categoryTitle TEXT,
                FOREIGN KEY (categoryId) REFERENCES dim_categories(categoryId)
            );

            CREATE TABLE dim_categories (
                categoryId TEXT PRIMARY KEY,
                categoryTitle TEXT
            );

            CREATE TABLE dim_topics (
                topicId TEXT PRIMARY KEY,
                topicTitle TEXT
            );

            CREATE TABLE fact_video_tags (
                videoId TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (videoId, tag),
                FOREIGN KEY (videoId) REFERENCES fact_videos(videoId)
            );

            CREATE TABLE fact_video_topics (
                videoId TEXT NOT NULL,
                topicId TEXT NOT NULL,
                topicTitle TEXT,
                PRIMARY KEY (videoId, topicId),
                FOREIGN KEY (videoId) REFERENCES fact_videos(videoId),
                FOREIGN KEY (topicId) REFERENCES dim_topics(topicId)
            );

            INSERT INTO dim_categories (categoryId, categoryTitle)
            SELECT DISTINCT v.categoryId, c.title
            FROM videos v
            LEFT JOIN youtube_categories c ON c.categoryId = v.categoryId
            WHERE v.categoryId IS NOT NULL;

            INSERT INTO fact_videos (
                videoId, title, description, channel, publishedAt,
                viewCount, likeCount, commentCount, duration, durationSeconds,
                categoryId, categoryTitle
            )
            SELECT
                v.videoId, v.title, v.description, v.channel, v.publishedAt,
                v.viewCount, v.likeCount, v.commentCount, v.duration, NULL,
                v.categoryId, c.categoryTitle
            FROM videos v
            LEFT JOIN dim_categories c ON c.categoryId = v.categoryId;
        """)

        videos = self.cursor.execute(
            "SELECT videoId, duration, tags, topicIds FROM videos"
        ).fetchall()

        video_durations = []
        topics = {}
        video_topics = []
        video_tags = []

        for video_id, duration, raw_tags, raw_topics in videos:
            video_durations.append((parse_duration_seconds(duration), video_id))

            try:
                tags = json.loads(raw_tags or "[]")
            except json.JSONDecodeError:
                tags = []

            for tag in tags:
                clean_tag = str(tag).strip()
                if clean_tag:
                    video_tags.append((video_id, clean_tag))

            try:
                topic_ids = json.loads(raw_topics or "[]")
            except json.JSONDecodeError:
                topic_ids = []

            for topic_id in topic_ids:
                topic_id = str(topic_id)
                topic_title = topic_id.rstrip("/").split("/")[-1].replace("_", " ")
                topics[topic_id] = topic_title
                video_topics.append((video_id, topic_id, topic_title))

        self.cursor.executemany("""
            UPDATE fact_videos
            SET durationSeconds = ?
            WHERE videoId = ?
        """, video_durations)

        self.cursor.executemany("""
            INSERT OR IGNORE INTO fact_video_tags (videoId, tag)
            VALUES (?, ?)
        """, video_tags)

        self.cursor.executemany("""
            INSERT OR REPLACE INTO dim_topics (topicId, topicTitle)
            VALUES (?, ?)
        """, topics.items())

        self.cursor.executemany("""
            INSERT OR IGNORE INTO fact_video_topics (videoId, topicId, topicTitle)
            VALUES (?, ?, ?)
        """, video_topics)

        self.conn.commit()

        return {
            'fact_videos': self.cursor.execute(
                "SELECT COUNT(*) FROM fact_videos"
            ).fetchone()[0],
            'dim_categories': self.cursor.execute(
                "SELECT COUNT(*) FROM dim_categories"
            ).fetchone()[0],
            'dim_topics': self.cursor.execute(
                "SELECT COUNT(*) FROM dim_topics"
            ).fetchone()[0],
            'fact_video_tags': self.cursor.execute(
                "SELECT COUNT(*) FROM fact_video_tags"
            ).fetchone()[0],
            'fact_video_topics': self.cursor.execute(
                "SELECT COUNT(*) FROM fact_video_topics"
            ).fetchone()[0],
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()


if __name__ == "__main__":
    loader = YouTubeDataLoader()
    
    print("\n📊 Loading YouTube data into SQLite...\n")
    
    loader.create_table()
    stats = loader.load_from_json_files()
    
    print(f"\n✅ Load complete!")
    print(f"   Total loaded: {stats['total_loaded']}")
    print(f"   Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"   From {stats['batch_files']} batch files")
    
    print(f"\n📈 Data statistics:")
    data_stats = loader.get_stats()
    print(f"   Total videos: {data_stats['total_videos']}")
    print(f"   Avg views: {data_stats['avg_views']:,}")
    print(f"   Max views: {data_stats['max_views']:,}")
    print(f"   Min views: {data_stats['min_views']:,}")
    print(f"\n   Top 5 channels:")
    for channel, count in data_stats['top_channels']:
        print(f"     - {channel}: {count} videos")

    print(f"\n⭐ Building modeled tables:")
    model_stats = loader.build_modeled_tables()
    for table_name, row_count in model_stats.items():
        print(f"   {table_name}: {row_count}")
    
    print(f"\n   Database saved to: data/processed/heated_rivalry.db")
    
    loader.close()
