"""General helper functions for data manipulation and parsing."""

import re
from typing import Any, Dict


def extract_v_page(video: Dict[str, Any]) -> int:
    """Extract integer page number safely from video dictionary item."""
    if not isinstance(video, dict):
        return 0

    fp = video.get("forum_page")
    if fp:
        try:
            return int(fp)
        except (ValueError, TypeError):
            pass

    source_page = video.get("source_page") or ""
    m = re.search(r"page-(\d+)", source_page)
    if m:
        try:
            return int(m.group(1))
        except (ValueError, TypeError):
            pass

    return 0


def hero_rank_key(video: Dict[str, Any]) -> tuple:
    """Generate sorting tuple for selecting hero featured videos.

    Ranks by: (page_number DESC, has_thumbnail DESC, video_id DESC)
    """
    page = extract_v_page(video)
    thumb = video.get("thumbnail_url") or ""
    has_thumb = 1 if (thumb and len(thumb) > 10 and "/placeholder" not in thumb) else 0
    vid_id = video.get("id", 0)
    try:
        vid_id_int = int(vid_id)
    except (ValueError, TypeError):
        vid_id_int = 0

    return (page, has_thumb, vid_id_int)


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to int with fallback default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
