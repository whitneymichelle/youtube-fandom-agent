"""
Fetch a batch of YouTube video metadata and save it to data/raw/
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.youtube_api.fetcher import YouTubeDataFetcher


def main() -> None:
    load_dotenv()

    fetcher = YouTubeDataFetcher(os.getenv("YOUTUBE_API_KEY"))

    print("\n🎬 Fetching YouTube videos...\n")

    result = fetcher.search_videos_batch(
        query="heated rivalry",
        target_count=1000,
        output_dir="data/raw"
    )

    print(f"\n✅ Complete!")
    print(f"   Total videos: {result['total_videos']}")
    print(f"   API requests: {result['batches']}")
    print(f"   Quota used: {result['quota_used']} (~{result['quota_used']/100:.1f}% of daily limit)")
    print(f"   Files saved: {len(result['files_saved'])}")
    print(f"\n   Files:")
    for f in result['files_saved']:
        print(f"     - {f}")


if __name__ == "__main__":
    main()
