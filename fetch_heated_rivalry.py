"""
Fetch 1,000 "heated rivalry" videos and save to data/raw/
"""

import os
from dotenv import load_dotenv
from src.youtube_api.fetcher import YouTubeDataFetcher

load_dotenv()

fetcher = YouTubeDataFetcher(os.getenv("YOUTUBE_API_KEY"))

print("\n🎬 Fetching 1,000 'heated rivalry' videos...\n")

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
