"""Backward compatibility wrapper for scraper.py.

Re-exports scraper functions and thread configurations from the modular service layer.
"""

from config import THREADS, VIDEO_HOSTS, VIDEO_KEYWORDS
from app.services.scraper_service import (
    is_video_link,
    get_base_thread_url,
    get_latest_page_number,
    extract_videos_from_page,
    is_cdp_ready,
    scrape_live_page,
)

__all__ = [
    "THREADS",
    "VIDEO_HOSTS",
    "VIDEO_KEYWORDS",
    "is_video_link",
    "get_base_thread_url",
    "get_latest_page_number",
    "extract_videos_from_page",
    "is_cdp_ready",
    "scrape_live_page",
]

if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Realtime Playwright scraper for forum thread pages")
    parser.add_argument("--page", type=int, default=None, help="Target forum page number")
    parser.add_argument("--thread", default="live_show", choices=list(THREADS.keys()), help="Target thread key")
    args = parser.parse_args()

    try:
        data = scrape_live_page(target_page_num=args.page, thread_key=args.thread)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        sys.stderr.write(f"Scraper error: {e}\n")
        sys.exit(1)
