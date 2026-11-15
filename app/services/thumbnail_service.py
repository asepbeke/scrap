"""Thumbnail Downloader Service.

Handles concurrent image downloads with customizable headers, referer matching,
and progress reporting for local media archiving.
"""

import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests

from config import BASE_DIR, THREADS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
}


class ThumbnailService:
    """Service for batch downloading video thumbnail images."""

    @staticmethod
    def download_single(item: Tuple[int, str], target_dir: Path) -> Tuple[bool, int, str]:
        """Download single thumbnail file with timeout and referer."""
        video_id, image_url = item
        if not image_url or not image_url.startswith("http"):
            return False, video_id, "Invalid URL"

        target_path = target_dir / f"{video_id}.jpg"
        if target_path.exists() and target_path.stat().st_size > 1024:
            return True, video_id, "Already exists"

        try:
            parsed = urlparse(image_url)
            custom_headers = dict(HEADERS)
            custom_headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

            response = requests.get(image_url, headers=custom_headers, timeout=12)
            if response.status_code == 200 and len(response.content) > 500:
                target_path.write_bytes(response.content)
                return True, video_id, "Success"
            return False, video_id, f"HTTP {response.status_code}"
        except Exception as e:
            return False, video_id, str(e)

    @classmethod
    def download_all(
        cls,
        thread_key: str = "live_show",
        base_dir: Optional[Path] = None,
        max_workers: int = 12,
        progress_cb: Optional[Callable[[int, int, int, int, int], None]] = None
    ) -> Dict[str, Any]:
        """Download all thumbnails for videos in the selected thread database."""
        base_path = base_dir or BASE_DIR
        cfg = THREADS.get(thread_key, THREADS["live_show"])
        db_path = base_path / cfg["db_file"]
        target_dir = base_path / "static" / "thumbnails"
        target_dir.mkdir(parents=True, exist_ok=True)

        if not db_path.exists():
            return {"total": 0, "success": 0, "already": 0, "failed": 0, "error": f"{db_path.name} not found"}

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT id, image_url FROM videos WHERE image_url IS NOT NULL AND image_url != ''").fetchall()
        conn.close()

        total = len(rows)
        success_count = 0
        fail_count = 0
        already_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(cls.download_single, row, target_dir): row[0]
                for row in rows
            }

            completed = 0
            for future in as_completed(future_to_id):
                completed += 1
                ok, v_id, msg = future.result()
                if ok:
                    if msg == "Already exists":
                        already_count += 1
                    else:
                        success_count += 1
                else:
                    fail_count += 1

                if progress_cb and (completed % 25 == 0 or completed == total):
                    progress_cb(completed, total, success_count, already_count, fail_count)

        return {
            "total": total,
            "success": success_count,
            "already": already_count,
            "failed": fail_count,
            "target_dir": str(target_dir),
        }
