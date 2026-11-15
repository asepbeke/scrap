"""CLI script for downloading video thumbnails across threads."""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import THREADS, BASE_DIR
from app.services.thumbnail_service import ThumbnailService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("download_thumbs")


def progress_reporter(completed: int, total: int, success: int, already: int, failed: int):
    print(f"[{completed}/{total}] Downloaded: {success} | Exists: {already} | Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(description="Download video thumbnails to local disk")
    parser.add_argument("--thread", default="live_show", choices=list(THREADS.keys()), help="Target thread key")
    parser.add_argument("--all", action="store_true", help="Download thumbnails for all threads")
    parser.add_argument("--workers", type=int, default=12, help="Concurrent download threads (default: 12)")

    args = parser.parse_args()

    threads_to_process = list(THREADS.keys()) if args.all else [args.thread]

    for t_key in threads_to_process:
        logger.info("Processing thumbnails for [%s]...", THREADS[t_key]["name"])
        res = ThumbnailService.download_all(
            thread_key=t_key,
            base_dir=BASE_DIR,
            max_workers=args.workers,
            progress_cb=progress_reporter,
        )
        logger.info(
            "Completed [%s]: Total %d | New %d | Existing %d | Failed %d",
            t_key, res["total"], res["success"], res["already"], res["failed"]
        )


if __name__ == "__main__":
    main()
