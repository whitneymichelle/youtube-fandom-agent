"""
YouTube API data fetching module.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeDataFetcher:
    """
    Fetches video data from YouTube API.

    Each search() call costs ~100 quota units. YouTube API has 10,000 quota/day.
    Default max_results=5 keeps costs low for exploration.
    """

    def __init__(self, api_key: str):
        """
        Initialize the YouTube Data Fetcher.

        Args:
            api_key: YouTube API key from Google Cloud Console
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def search_videos(
        self,
        query: str,
        max_results: int = 5,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search for videos on YouTube.

        Args:
            query: Search query string (e.g., "heated rivalry")
            max_results: Max videos to return. Default=5 to save quota.
                        API cost: ~100 quota per request, 10k quota/day limit.
            order: "relevance" (default), "viewCount", "date", "rating"

        Returns:
            List of video data dicts with keys:
            - videoId, title, description, channel, publishedAt,
              viewCount, likeCount, commentCount, duration,
              tags (JSON array), categoryId, topicIds (JSON array)

        Raises:
            HttpError: If API call fails
        """
        try:
            # Step 1: Search for videos
            search_response = self.youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results,
                order=order
            ).execute()

            # Extract video IDs from search results
            video_ids = [
                item['id']['videoId']
                for item in search_response.get('items', [])
            ]

            if not video_ids:
                return []

            # Step 2: Get detailed stats (views, likes, etc) for each video
            stats_response = self.youtube.videos().list(
                id=','.join(video_ids),
                part="statistics,snippet,contentDetails,topicDetails"
            ).execute()

            # Step 3: Extract and structure the data
            videos = []
            for video in stats_response.get('items', []):
                # Extract tags (list of strings, store as JSON)
                tags = video['snippet'].get('tags', [])
                
                # Extract category ID
                category_id = video['snippet'].get('categoryId', None)
                
                # Extract topic categories (list of Wikipedia URLs)
                topic_categories = video.get('topicDetails', {}).get('topicCategories', [])
                
                video_data = {
                    'videoId': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'channel': video['snippet']['channelTitle'],
                    'publishedAt': video['snippet']['publishedAt'],
                    'viewCount': int(video['statistics'].get('viewCount', 0)),
                    'likeCount': int(video['statistics'].get('likeCount', 0)),
                    'commentCount': int(video['statistics'].get('commentCount', 0)),
                    'duration': video.get('contentDetails', {}).get('duration'),
                    'tags': json.dumps(tags),
                    'categoryId': category_id,
                    'topicIds': json.dumps(topic_categories),
                }
                videos.append(video_data)

            return videos

        except HttpError as e:
            raise HttpError(
                resp=e.resp,
                content=e.content,
                uri=e.uri
            ) from e
    
    def search_videos_batch(
        self,
        query: str,
        target_count: int = 1000,
        output_dir: str = "data/raw"
    ) -> Dict[str, Any]:
        """
        Fetch multiple batches of videos with pagination.
        Saves each batch to JSON file as checkpoint.
        
        Args:
            query: Search query (e.g., "heated rivalry")
            target_count: Target number of videos to fetch (default 1000)
            output_dir: Directory to save batch JSON files
            
        Returns:
            Dict with keys:
            - total_videos: Number of videos fetched
            - batches: Number of API requests made
            - quota_used: Estimated quota used (~100 per batch)
            - files_saved: List of saved JSON file paths
            
        Raises:
            HttpError: If API call fails
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        videos = []
        next_page_token = None
        batch_num = 1
        files_saved = []
        
        try:
            while len(videos) < target_count:
                # Search with pagination
                search_response = self.youtube.search().list(
                    q=query,
                    part="snippet",
                    type="video",
                    maxResults=50,  # Max allowed by API
                    pageToken=next_page_token,
                    order="relevance"
                ).execute()
                
                # Extract video IDs
                batch_video_ids = [
                    item['id']['videoId']
                    for item in search_response.get('items', [])
                ]
                
                if not batch_video_ids:
                    break
                
                # Get stats for this batch
                stats_response = self.youtube.videos().list(
                    id=','.join(batch_video_ids),
                    part="statistics,snippet,contentDetails,topicDetails"
                ).execute()
                
                # Structure the data
                batch_videos = []
                for video in stats_response.get('items', []):
                    # Extract tags
                    tags = video['snippet'].get('tags', [])
                    
                    # Extract category ID
                    category_id = video['snippet'].get('categoryId', None)
                    
                    # Extract topic categories
                    topic_categories = video.get('topicDetails', {}).get('topicCategories', [])
                    
                    video_data = {
                        'videoId': video['id'],
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'],
                        'channel': video['snippet']['channelTitle'],
                        'publishedAt': video['snippet']['publishedAt'],
                        'viewCount': int(video['statistics'].get('viewCount', 0)),
                        'likeCount': int(video['statistics'].get('likeCount', 0)),
                        'commentCount': int(video['statistics'].get('commentCount', 0)),
                        'duration': video.get('contentDetails', {}).get('duration'),
                        'tags': json.dumps(tags),
                        'categoryId': category_id,
                        'topicIds': json.dumps(topic_categories),
                    }
                    videos.append(video_data)
                    batch_videos.append(video_data)
                
                # Save batch to file
                batch_file = Path(output_dir) / f"{query.replace(' ', '_')}_batch_{batch_num}.json"
                with open(batch_file, 'w') as f:
                    json.dump(batch_videos, f, indent=2)
                files_saved.append(str(batch_file))
                
                print(f"Batch {batch_num}: Fetched {len(batch_videos)} videos "
                      f"(Total: {len(videos)}/{target_count})")
                
                # Get next page token for pagination
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                batch_num += 1
            
            return {
                'total_videos': len(videos),
                'batches': len(files_saved),
                'quota_used': len(files_saved) * 100,
                'files_saved': files_saved
            }
            
        except HttpError as e:
            raise HttpError(
                resp=e.resp,
                content=e.content,
                uri=e.uri
            ) from e
