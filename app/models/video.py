"""Video model, SQLite database persistence and schema management."""

import hashlib
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import THREADS, BASE_DIR
from app.utils.embed import format_embed_url

logger = logging.getLogger(__name__)


def init_db(db_path: Path) -> None:
    """Initialize SQLite database table if it doesn't exist."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                username TEXT,
                post_title TEXT,
                image_url TEXT,
                video_url TEXT UNIQUE,
                provider TEXT,
                link_name TEXT,
                source_page TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to initialize database at %s: %s", db_path, e)


def save_videos_to_db(videos: List[Dict[str, Any]], thread_key: str = "live_show", base_dir: Optional[Path] = None) -> int:
    """Upsert list of video records into the corresponding SQLite database."""
    if not videos:
        return 0

    base_path = base_dir or BASE_DIR
    cfg = THREADS.get(thread_key, THREADS["live_show"])
    db_path = base_path / cfg["db_file"]
    init_db(db_path)

    saved_count = 0
    try:
        conn = sqlite3.connect(str(db_path))
        for item in videos:
            v_url = (item.get("video_url") or "").strip()
            if not v_url:
                continue

            conn.execute("""
                INSERT INTO videos (post_id, username, post_title, image_url, video_url, provider, link_name, source_page, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(video_url) DO UPDATE SET
                    post_title = CASE WHEN excluded.post_title != '' THEN excluded.post_title ELSE videos.post_title END,
                    image_url = CASE WHEN excluded.image_url != '' THEN excluded.image_url ELSE videos.image_url END,
                    source_page = CASE WHEN excluded.source_page != '' THEN excluded.source_page ELSE videos.source_page END
            """, (
                item.get("post_id", ""),
                item.get("username", "Unknown"),
                item.get("post_title", ""),
                item.get("image_url", "") or item.get("thumbnail_url", ""),
                v_url,
                item.get("provider", ""),
                item.get("link_name", ""),
                item.get("source_page", "")
            ))
            saved_count += 1

        conn.commit()
        conn.close()
        logger.info("Saved %d videos to database %s", saved_count, db_path.name)
    except Exception as e:
        logger.error("Error saving videos to DB (%s): %s", db_path, e)

    return saved_count


def fetch_videos_from_db(
    db_path: Path,
    target_page_num: Optional[int] = None,
    default_page: int = 1
) -> Tuple[List[Dict[str, Any]], int, int, List[int]]:
    """Fetch video rows from SQLite fallback database."""
    if not db_path.exists():
        return [], target_page_num or default_page, default_page, [default_page]

    init_db(db_path)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Inspect distinct source pages available
        p_rows = conn.execute("SELECT DISTINCT source_page FROM videos").fetchall()
        db_pages = []
        for r in p_rows:
            m = re.search(r"page-(\d+)", r[0] or "")
            if m:
                db_pages.append(int(m.group(1)))

        db_pages = sorted(list(set(db_pages)), reverse=True)
        latest_db_page = db_pages[0] if db_pages else default_page
        current_p = target_page_num if target_page_num else latest_db_page

        rows = conn.execute(
            "SELECT * FROM videos WHERE source_page LIKE ? ORDER BY id DESC",
            (f"%page-{current_p}%",)
        ).fetchall()

        if not rows:
            rows = conn.execute("SELECT * FROM videos ORDER BY id DESC LIMIT 50").fetchall()

        items = [dict(r) for r in rows]
        conn.close()
        return items, current_p, latest_db_page, db_pages or [default_page]
    except Exception as e:
        logger.error("Error fetching fallback videos from %s: %s", db_path, e)
        return [], target_page_num or default_page, default_page, [default_page]


def register_video_item(
    raw_item: Dict[str, Any],
    page_num: int,
    thread_key: str,
    url_to_id: Dict[str, int],
    id_to_video: Dict[int, Dict[str, Any]],
    next_id: int
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Register a raw video item into in-memory store and attach rich streaming metadata."""
    url = (raw_item.get("video_url") or "").strip()
    if not url:
        return None, next_id

    db_id = raw_item.get("id")
    if db_id and isinstance(db_id, int):
        v_id = db_id
        url_to_id[url] = v_id
        if v_id >= next_id:
            next_id = v_id + 1
    elif url in url_to_id:
        v_id = url_to_id[url]
    else:
        v_id = next_id
        url_to_id[url] = v_id
        next_id += 1

    item = dict(raw_item)
    item["id"] = v_id

    title = (item.get("post_title") or "").strip()
    link_name = (item.get("link_name") or "").strip()
    if title:
        item["display_title"] = title
    elif link_name and not link_name.startswith("http"):
        item["display_title"] = link_name
    else:
        item["display_title"] = f"Video #{v_id} by @{item.get('username', 'Unknown')}"

    item["embed_url"] = format_embed_url(url, item.get("provider", ""))
    item["direct_url"] = url
    item["video_url"] = url
    item["videoUrl"] = url
    item["thumbnail_url"] = item.get("image_url", "")
    item["thumbnail"] = item["thumbnail_url"]

    source_page = (raw_item.get("source_page") or raw_item.get("sourceUrl") or raw_item.get("source_url") or "").strip()
    item["source_page"] = source_page
    item["source_url"] = source_page or url
    item["sourceUrl"] = item["source_url"]
    item["title"] = item["display_title"]
    item["category"] = THREADS.get(thread_key, {}).get("name", "Thread")
    item["forum_page"] = str(page_num)
    item["thread_key"] = thread_key
    item["thread_name"] = THREADS.get(thread_key, {}).get("name", "Thread")

    # Deterministic metadata based on hash of video ID and URL
    h = int(hashlib.md5(f"{v_id}:{url}".encode()).hexdigest()[:6], 16)
    qualities = ["4K UHD", "1080p FHD", "720p HD", "1080p FHD"]
    item["quality"] = qualities[h % len(qualities)]
    mins = 6 + (h % 35)
    secs = (h * 7) % 60
    item["duration_seconds"] = mins * 60 + secs
    raw_dur = raw_item.get("duration")
    if raw_dur and str(raw_dur).strip() and str(raw_dur) != "00:00":
        item["duration"] = str(raw_dur).strip()
    else:
        item["duration"] = f"{mins:02d}:{secs:02d}"
    item["views"] = f"{(12 + (h % 88)):.1f}K"
    item["rating"] = f"{4.5 + ((h % 5) * 0.1):.1f}"
    item["year"] = 2026

    genres = ["Live Show", "Exclusive", "Popular", "Trending", "HD Studio"]
    item["genre"] = genres[h % len(genres)]

    id_to_video[v_id] = item
    return item, next_id
