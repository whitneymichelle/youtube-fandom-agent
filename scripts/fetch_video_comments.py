#!/usr/bin/env python3
"""
Fetch YouTube comment threads for existing video IDs.

This script is intentionally separate from the metadata fetcher because the project
stores commentCount but does not currently store comment text. Use it to add a
second data collection step for comment analysis.

Examples:
  python scripts/fetch_video_comments.py
  python scripts/fetch_video_comments.py --video-ids data/video_ids.txt
  python scripts/fetch_video_comments.py --from-json data/raw --output-dir data/comments
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
from dotenv import load_dotenv


COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
COMMENTS_URL = "https://www.googleapis.com/youtube/v3/comments"


def load_env_api_key(api_key: Optional[str]) -> str:
    if api_key:
        return api_key
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError(
            "No YouTube API key found. Set YOUTUBE_API_KEY in your environment or .env file."
        )
    return api_key


def extract_video_ids_from_json_file(path: Path) -> Set[str]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return set()

    ids: Set[str] = set()

    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("items") or payload.get("videos") or []
    else:
        items = []

    for item in items:
        video_id = item.get("videoId") or item.get("id")
        if isinstance(video_id, str) and video_id.strip():
            ids.add(video_id.strip())

    return ids


def load_video_ids_from_dir(raw_dir: str) -> Set[str]:
    base_dir = Path(raw_dir)
    if not base_dir.exists():
        raise FileNotFoundError(f"Video JSON dir not found: {raw_dir}")

    ids: Set[str] = set()
    for path in sorted(base_dir.glob("*.json")):
        ids |= extract_video_ids_from_json_file(path)

    return ids


def load_video_ids_from_text_file(path: str) -> Set[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Video ID file not found: {path}")

    ids: Set[str] = set()
    for line in file_path.read_text().splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            ids.add(value)
    return ids


def normalize_comment(comment: Dict[str, Any], video_id: str) -> Dict[str, Any]:
    snippet = comment.get("snippet", {})
    top_level = snippet.get("topLevelComment", {}).get("snippet", {})
    reply_comment = snippet.get("replyComment", {})
    if reply_comment:
        reply_snippet = reply_comment.get("snippet", {})
        text = reply_snippet.get("textDisplay") or reply_snippet.get("textOriginal") or ""
        author = reply_snippet.get("authorDisplayName") or "unknown"
        published_at = reply_snippet.get("publishedAt")
        like_count = reply_snippet.get("likeCount", 0)
        root_id = reply_snippet.get("parentId") or comment.get("id")
        is_reply = True
    else:
        text = top_level.get("textDisplay") or top_level.get("textOriginal") or ""
        author = top_level.get("authorDisplayName") or "unknown"
        published_at = top_level.get("publishedAt")
        like_count = top_level.get("likeCount", 0)
        root_id = comment.get("id")
        is_reply = False

    return {
        "video_id": video_id,
        "thread_id": comment.get("id") or comment.get("commentThreadId"),
        "comment_id": comment.get("id") or comment.get("commentId"),
        "parent_comment_id": root_id,
        "author": author,
        "published_at": published_at,
        "like_count": int(like_count or 0),
        "text": text,
        "is_reply": is_reply,
        "source": "youtube_commentThreads",
    }


def fetch_comment_threads_for_video(api_key: str, video_id: str, max_pages: int = 10, max_results: int = 100) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": max_results,
        "key": api_key,
        "textFormat": "plainText",
    }

    all_comments: List[Dict[str, Any]] = []
    errors: List[str] = []
    page_token: Optional[str] = None

    for page_index in range(max_pages):
        if page_token:
            params["pageToken"] = page_token
        else:
            params.pop("pageToken", None)

        response = requests.get(COMMENT_THREADS_URL, params=params, timeout=60)
        payload = response.json()

        if response.status_code >= 400:
            errors.append(json.dumps({"video_id": video_id, "status": response.status_code, "payload": payload}))
            break

        items = payload.get("items", [])
        for item in items:
            try:
                snippet = item.get("snippet", {})
                top_level = snippet.get("topLevelComment", {})
                top_level_snippet = top_level.get("snippet", {})
                comment_id = top_level.get("id") or item.get("id")
                top_level_record = {
                    "video_id": video_id,
                    "thread_id": item.get("id"),
                    "comment_id": comment_id,
                    "parent_comment_id": None,
                    "author": top_level_snippet.get("authorDisplayName") or "unknown",
                    "published_at": top_level_snippet.get("publishedAt"),
                    "like_count": int(top_level_snippet.get("likeCount", 0) or 0),
                    "text": top_level_snippet.get("textDisplay") or top_level_snippet.get("textOriginal") or "",
                    "is_reply": False,
                    "source": "youtube_commentThreads",
                }
                all_comments.append(top_level_record)

                replies = item.get("replies", {}).get("comments", [])
                for reply in replies:
                    reply_snippet = reply.get("snippet", {})
                    reply_record = {
                        "video_id": video_id,
                        "thread_id": item.get("id"),
                        "comment_id": reply.get("id"),
                        "parent_comment_id": comment_id,
                        "author": reply_snippet.get("authorDisplayName") or "unknown",
                        "published_at": reply_snippet.get("publishedAt"),
                        "like_count": int(reply_snippet.get("likeCount", 0) or 0),
                        "text": reply_snippet.get("textDisplay") or reply_snippet.get("textOriginal") or "",
                        "is_reply": True,
                        "source": "youtube_commentThreads",
                    }
                    all_comments.append(reply_record)
            except Exception as exc:  # pragma: no cover - defensive, not mutating
                errors.append(json.dumps({"video_id": video_id, "error": str(exc), "item": item}))

        if not payload.get("nextPageToken"):
            break

        page_token = payload.get("nextPageToken")

    return {
        "video_id": video_id,
        "comment_count": len(all_comments),
        "comments": all_comments,
        "errors": errors,
        "status": "ok" if not errors else "partial",
    }


def write_jsonl(output_file: Path, rows: Iterable[Dict[str, Any]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch YouTube comments for existing video IDs.")
    parser.add_argument("--video-ids", help="Text file with one video ID per line, or a JSON file with a list of objects/IDs.")
    parser.add_argument("--from-json", default="data/raw", help="Directory containing raw JSON files with videoId values.")
    parser.add_argument("--output-dir", default="data/comments", help="Directory to write comments JSONL output.")
    parser.add_argument("--api-key", help="Optional YouTube API key; otherwise reads YOUTUBE_API_KEY from .env or environment.")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to fetch per video (default: 10).")
    parser.add_argument("--max-results", type=int, default=100, help="Max result count per page (1 to 100).")
    parser.add_argument("--limit", type=int, default=None, help="Optional cap on number of video IDs to process.")
    parser.add_argument("--batch-size", type=int, default=None, help="Process only this many video IDs in a single batch.")
    parser.add_argument("--batch-offset", type=int, default=0, help="Starting offset for batch processing.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned batch size and estimated quota without making API requests.")
    args = parser.parse_args()

    try:
        api_key = load_env_api_key(args.api_key)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        if args.video_ids:
            if args.video_ids.endswith(".json"):
                ids = extract_video_ids_from_json_file(Path(args.video_ids))
            else:
                ids = load_video_ids_from_text_file(args.video_ids)
        else:
            ids = load_video_ids_from_dir(args.from_json)
    except (FileNotFoundError, OSError) as exc:
        print(f"Error loading video IDs: {exc}", file=sys.stderr)
        return 1

    ids = sorted(ids)
    if args.limit is not None:
        ids = ids[: args.limit]

    if args.batch_size is not None:
        if args.batch_size <= 0:
            print("--batch-size must be greater than 0.", file=sys.stderr)
            return 1
        if args.batch_offset < 0:
            print("--batch-offset must be >= 0.", file=sys.stderr)
            return 1
        start = args.batch_offset
        end = start + args.batch_size
        ids = ids[start:end]

    if not ids:
        print("No video IDs found. Check --video-ids or --from-json.", file=sys.stderr)
        return 1

    if args.dry_run:
        estimated_requests = len(ids) * max(1, args.max_pages)
        print(f"Dry run: {len(ids)} video IDs selected")
        print(f"Estimated API requests: {estimated_requests}")
        print(f"Estimated quota use: ~{estimated_requests} units (1 unit per commentThreads request)")
        if args.batch_size is not None:
            print(f"Batch window: offset={args.batch_offset}, size={args.batch_size}")
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"comments_{timestamp}.jsonl"

    all_records: List[Dict[str, Any]] = []
    counts = Counter()
    status_counts = Counter()

    print(f"Fetching comments for {len(ids)} video IDs...")
    for index, video_id in enumerate(ids, start=1):
        print(f"[{index}/{len(ids)}] video_id={video_id}")
        result = fetch_comment_threads_for_video(api_key, video_id, max_pages=args.max_pages, max_results=args.max_results)
        status_counts[result["status"]] += 1
        counts["videos_processed"] += 1
        counts["comments_fetched"] += result["comment_count"]
        all_records.extend(result["comments"])

    write_jsonl(output_file, all_records)

    print("\n✅ Complete")
    print(f"  Output file: {output_file}")
    print(f"  Videos processed: {counts['videos_processed']}")
    print(f"  Comments fetched: {counts['comments_fetched']}")
    print(f"  Status counts: {dict(status_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
