"""Unified CLI Batch Scraper for forum threads.

Extracts video posts across a range of pages and persists them into SQLite and CSV.
Supports custom page ranges and thread selection.
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright

# Add parent directory to sys.path so config and app can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BASE_DIR, THREADS
from app.services.scraper_service import (
    extract_videos_from_page,
    get_base_thread_url,
    get_latest_page_number,
    is_cdp_ready,
)
from app.models.video import save_videos_to_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("batch_scrape")


def save_csv(results: list, csv_path: Path) -> None:
    """Save extracted video list to CSV file."""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "post_id",
                "username",
                "post_title",
                "image_url",
                "provider",
                "video_url",
                "link_name",
                "source_page"
            ],
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(results)


def run_batch_scrape(
    thread_key: str = "live_show",
    num_pages: int = 10,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    custom_page: Optional[int] = None
) -> None:
    """Execute batch scraping across target pages for the specified thread."""
    if not is_cdp_ready():
        logger.error("Chrome is not running on port 9222. Please start Chrome with --remote-debugging-port=9222")
        sys.exit(1)

    thread_info = THREADS.get(thread_key, THREADS["live_show"])
    target_thread_id = thread_info["thread_id"]
    db_file = BASE_DIR / thread_info["db_file"]
    csv_file = BASE_DIR / thread_info["csv_file"]

    logger.info("Starting Batch Scraper for [%s]", thread_info["name"])

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]

        # 1. Search for tab specific to target thread
        page = next(
            (t for t in context.pages if target_thread_id in t.url and "Log in" not in t.title()),
            None
        )

        if page is None:
            page = next(
                (t for t in context.pages if ("/threads/" in t.url or "semprot.com" in t.url) and "Log in" not in t.title()),
                None
            )

        if page is None:
            logger.error("No authenticated forum tab found in Chrome.")
            sys.exit(1)

        logger.info("Connected to Tab: %s | URL: %s", page.title(), page.url)

        base_thread_url = get_base_thread_url(page.url)
        if not base_thread_url or target_thread_id not in base_thread_url:
            base_thread_url = thread_info["base_url"]

        latest_page = max(get_latest_page_number(page), thread_info["default_page"])

        # Determine start and end page
        if custom_page is not None:
            s_page = max(1, custom_page)
            e_page = s_page
        elif start_page is not None or end_page is not None:
            s_page = max(1, start_page or 1)
            e_page = end_page or latest_page
        else:
            s_page = max(1, latest_page - num_pages + 1)
            e_page = latest_page

        logger.info("Target pages: %d to %d (Total: %d pages)", s_page, e_page, e_page - s_page + 1)

        all_results = []
        for p_num in range(s_page, e_page + 1):
            target_url = f"{base_thread_url}/page-{p_num}"
            logger.info("[%d/%d] Navigating to: %s", p_num, e_page, target_url)

            if page.url.rstrip("/") != target_url.rstrip("/"):
                try:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_selector(".message", timeout=10000)
                except Exception as e:
                    logger.warning("Timeout/Notice on page %d: %s", p_num, e)

                page.wait_for_timeout(1000)

            page_videos = extract_videos_from_page(page)
            logger.info("-> Page %d yielded %d video links.", p_num, len(page_videos))
            all_results.extend(page_videos)

        # Deduplicate results
        unique_map = {item["video_url"]: item for item in all_results}
        final_results = list(unique_map.values())

        logger.info("Extracted %d unique video links across %d pages.", len(final_results), e_page - s_page + 1)

        # Save to SQLite and CSV
        saved_count = save_videos_to_db(final_results, thread_key=thread_key, base_dir=BASE_DIR)
        save_csv(final_results, csv_file)

        logger.info("Completed! %d items processed. DB: %s | CSV: %s", saved_count, db_file.name, csv_file.name)


def main():
    parser = argparse.ArgumentParser(description="StreamVault CLI Batch Forum Scraper")
    parser.add_argument("--thread", default="live_show", choices=list(THREADS.keys()), help="Target thread key")
    parser.add_argument("--pages", type=int, default=10, help="Number of latest pages to scrape (default: 10)")
    parser.add_argument("--start", type=int, default=None, help="Start page number")
    parser.add_argument("--end", type=int, default=None, help="End page number")
    parser.add_argument("--custom", type=int, default=None, help="Scrape single custom page")
    parser.add_argument("positional_args", nargs="*", type=int, help="Optional positional page arguments e.g. '100' or '100 105'")

    args = parser.parse_args()

    s_page = args.start
    e_page = args.end
    c_page = args.custom

    if args.positional_args:
        if len(args.positional_args) == 1:
            c_page = args.positional_args[0]
        elif len(args.positional_args) >= 2:
            s_page = args.positional_args[0]
            e_page = args.positional_args[1]

    run_batch_scrape(
        thread_key=args.thread,
        num_pages=args.pages,
        start_page=s_page,
        end_page=e_page,
        custom_page=c_page,
    )


if __name__ == "__main__":
    main()
