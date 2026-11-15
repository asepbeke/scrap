"""Video Service: Manages in-memory video state, caching, querying, and streaming ranking."""

import logging
import random
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import BASE_DIR, THREADS
from app.models.video import fetch_videos_from_db, init_db, register_video_item, save_videos_to_db
from app.services.scraper_service import scrape_live_page
from app.utils.helpers import extract_v_page, hero_rank_key

logger = logging.getLogger(__name__)


class VideoService:
    """Singleton service managing video persistence, in-memory cache, and ranking."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR
        self.url_to_id: Dict[str, int] = {}
        self.id_to_video: Dict[int, Dict[str, Any]] = {}
        self.page_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.thread_latest: Dict[str, int] = {
            "live_show": 741,
            "igo": 3016,
            "req_live": 1625,
        }
        self.thread_titles: Dict[str, str] = {
            k: v["name"] for k, v in THREADS.items()
        }
        self.thread_base_urls: Dict[str, str] = {
            k: v.get("base_url", "") for k, v in THREADS.items()
        }
        self.active_thread: str = "live_show"
        self.is_live_mode: bool = False
        self.last_scrape_error: str = ""
        self.next_id: int = 1

    def register_video(self, raw_item: Dict[str, Any], page_num: int, thread_key: str = "live_show") -> Optional[Dict[str, Any]]:
        """Register a video item in memory with calculated streaming metadata."""
        item, self.next_id = register_video_item(
            raw_item=raw_item,
            page_num=page_num,
            thread_key=thread_key,
            url_to_id=self.url_to_id,
            id_to_video=self.id_to_video,
            next_id=self.next_id,
        )
        return item

    def preload_db_videos(self, limit: int = 300, thread_key: str = "live_show") -> None:
        """Pre-populate in-memory cache from local SQLite database."""
        cfg = THREADS.get(thread_key, THREADS["live_show"])
        db_path = self.base_dir / cfg["db_file"]
        if not db_path.exists():
            return

        init_db(db_path)
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM videos ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            for r in rows:
                m = re.search(r"page-(\d+)", r["source_page"] or "")
                p_num = int(m.group(1)) if m else cfg["default_page"]
                self.register_video(dict(r), p_num, thread_key=thread_key)
            conn.close()
            logger.info("Preloaded %d videos from %s", len(rows), db_path.name)
        except Exception as e:
            logger.warning("Error preloading DB videos (%s): %s", db_path.name, e)

    def preload_all_threads(self, limit: int = 300) -> None:
        """Preload videos for all configured threads."""
        for t_key in THREADS:
            self.preload_db_videos(limit=limit, thread_key=t_key)

    def get_fallback_from_db(self, target_page_num: Optional[int] = None, thread_key: str = "live_show") -> Tuple[List[Dict[str, Any]], int, int, List[int]]:
        """Fetch fallback videos from local SQLite database."""
        cfg = THREADS.get(thread_key, THREADS["live_show"])
        db_path = self.base_dir / cfg["db_file"]
        raw_items, cur_p, lat_p, db_pages = fetch_videos_from_db(
            db_path=db_path,
            target_page_num=target_page_num,
            default_page=cfg["default_page"],
        )

        items = []
        for r in raw_items:
            v = self.register_video(r, cur_p, thread_key=thread_key)
            if v:
                items.append(v)

        return items, cur_p, lat_p, db_pages

    def get_page_data(
        self,
        thread_key: str = "live_show",
        page_num: Optional[int] = None,
        force_refresh: bool = False,
        provider_filter: str = "",
        uploader_filter: str = "",
        q_search: str = "",
        sort_order: str = "newest",
    ) -> Dict[str, Any]:
        """Orchestrate data extraction, live scraping, fallback, and video collections."""
        if thread_key not in THREADS:
            thread_key = "live_show"
        self.active_thread = thread_key
        curr_cfg = THREADS[thread_key]

        cache_key = f"{thread_key}:{page_num}" if page_num else None
        latest_known = self.thread_latest.get(thread_key, curr_cfg["default_page"])
        current_page_num = page_num or latest_known
        available_pages: List[int] = []
        live_videos: List[Dict[str, Any]] = []

        # 1. Check in-memory page cache
        if not force_refresh and cache_key and cache_key in self.page_cache:
            live_videos = self.page_cache[cache_key]
            current_page_num = page_num
            self.is_live_mode = True
            self.last_scrape_error = ""
        else:
            # 2. Attempt realtime Playwright scrape
            try:
                scrape_data = scrape_live_page(target_page_num=page_num, thread_key=thread_key)
                raw_videos = scrape_data["videos"]
                current_page_num = scrape_data["current_page"]
                latest_known = scrape_data["latest_page"]

                self.thread_latest[thread_key] = latest_known
                self.thread_titles[thread_key] = scrape_data["thread_title"]
                self.thread_base_urls[thread_key] = scrape_data["base_url"]

                live_videos = []
                for item in raw_videos:
                    reg = self.register_video(item, current_page_num, thread_key=thread_key)
                    if reg:
                        live_videos.append(reg)

                if live_videos:
                    self.page_cache[f"{thread_key}:{current_page_num}"] = live_videos
                    save_videos_to_db(live_videos, thread_key=thread_key, base_dir=self.base_dir)
                    self.is_live_mode = True
                    self.last_scrape_error = ""
                else:
                    # Scrape succeeded connecting to tab, but 0 videos found on this page
                    db_vids, _, _, db_pages = self.get_fallback_from_db(page_num, thread_key=thread_key)
                    if db_vids:
                        live_videos = db_vids
                        available_pages = db_pages
                    self.is_live_mode = True
                    self.last_scrape_error = f"Halaman {current_page_num} tidak memuat link video baru. Menampilkan data cadangan."
            except Exception as e:
                # Scraper CDP connection failed -> Fallback to database
                self.is_live_mode = False
                self.last_scrape_error = str(e)
                logger.info("Realtime scraping fallback to DB: %s", e)
                db_vids, current_page_num, latest_known, db_pages = self.get_fallback_from_db(page_num, thread_key=thread_key)
                live_videos = db_vids
                available_pages = db_pages

        # 3. Calculate page navigation numbers
        if not available_pages:
            if current_page_num >= latest_known - 8:
                start_p = max(1, latest_known - 9)
                available_pages = list(range(start_p, latest_known + 1))
            else:
                start_p = max(1, current_page_num - 4)
                end_p = min(latest_known, current_page_num + 4)
                available_pages = list(range(start_p, end_p + 1))
            available_pages.sort(reverse=True)

        # 4. Preset Custom Page Milestones
        if thread_key == "igo":
            milestones = [1, 500, 1000, 1500, 2000, 2500, 3000, 3016]
        elif thread_key == "req_live":
            milestones = [1, 200, 500, 800, 1000, 1200, 1500, 1625]
        else:
            milestones = [1, 50, 100, 200, 300, 500, 700, 741]

        quick_milestones = [m for m in milestones if m < latest_known]
        if latest_known not in quick_milestones:
            quick_milestones.append(latest_known)

        # 5. Filtering
        filtered_videos = list(live_videos)
        if provider_filter:
            filtered_videos = [v for v in filtered_videos if provider_filter in (v.get("provider") or "").lower()]
        if uploader_filter:
            filtered_videos = [v for v in filtered_videos if uploader_filter in (v.get("username") or "").lower()]
        if q_search:
            page_filtered = [
                v for v in filtered_videos
                if q_search in (v.get("display_title") or "").lower()
                or q_search in (v.get("username") or "").lower()
                or q_search in (v.get("post_id") or "").lower()
            ]
            if page_filtered:
                filtered_videos = page_filtered
            else:
                # Search across all loaded videos for this thread
                all_known_thread = [v for v in self.id_to_video.values() if v.get("thread_key") == thread_key]
                filtered_videos = [
                    v for v in all_known_thread
                    if q_search in (v.get("display_title") or "").lower()
                    or q_search in (v.get("username") or "").lower()
                    or q_search in (v.get("post_id") or "").lower()
                ]

        # 6. Sorting
        if sort_order == "oldest":
            filtered_videos = sorted(filtered_videos, key=lambda x: x["id"])
        elif sort_order == "random":
            filtered_videos = list(filtered_videos)
            random.shuffle(filtered_videos)
        elif sort_order == "popular":
            filtered_videos = sorted(filtered_videos, key=lambda x: x.get("views", "0"), reverse=True)
        else:
            filtered_videos = sorted(filtered_videos, key=lambda x: x["id"], reverse=True)

        # 7. Provider counts for active page
        provider_counts: Dict[str, int] = {}
        for v in live_videos:
            p = v.get("provider")
            if p:
                provider_counts[p] = provider_counts.get(p, 0) + 1

        # 8. Video collections (Hero, Trending, Recommended, Recent, Popular)
        all_known = list(self.id_to_video.values())
        thread_vids = [v for v in all_known if v.get("thread_key") == thread_key]
        if not thread_vids:
            thread_vids = all_known

        sorted_hero = sorted(thread_vids, key=hero_rank_key, reverse=True)
        featured_videos = sorted_hero[:6] if sorted_hero else all_known[:6]

        valid_thumb_videos = [v for v in thread_vids if v.get("thumbnail_url") and len(v["thumbnail_url"]) > 10]
        if not valid_thumb_videos:
            valid_thumb_videos = thread_vids

        trending_videos = sorted(valid_thumb_videos, key=lambda x: x.get("views", "0"), reverse=True)[:10]
        recent_videos = sorted(valid_thumb_videos, key=lambda v: (extract_v_page(v), v.get("id", 0)), reverse=True)[:12]
        recommended_videos = [v for v in valid_thumb_videos if v not in trending_videos[:5]][:12]
        if not recommended_videos:
            recommended_videos = valid_thumb_videos[:10]
        popular_videos = sorted(valid_thumb_videos, key=lambda x: x.get("views", "0"), reverse=True)[:12]

        return {
            "videos": filtered_videos,
            "total_count": len(filtered_videos),
            "current_forum_page": current_page_num,
            "latest_page": latest_known,
            "available_pages": available_pages,
            "quick_milestones": quick_milestones,
            "selected_provider": provider_filter,
            "uploader": uploader_filter,
            "q": q_search,
            "sort": sort_order,
            "provider_counts": provider_counts,
            "is_live": self.is_live_mode,
            "last_error": self.last_scrape_error,
            "thread_title": self.thread_titles.get(thread_key, curr_cfg["name"]),
            "active_thread": thread_key,
            "threads": THREADS,
            "current_thread_cfg": curr_cfg,
            "featured_videos": featured_videos,
            "trending_videos": trending_videos,
            "recommended_videos": recommended_videos,
            "popular_videos": popular_videos,
            "recent_videos": recent_videos,
        }

    def get_video_detail(self, video_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Fetch video by ID with adjacent navigation and recommendation lists."""
        video = self.id_to_video.get(video_id)
        if not video:
            for t_key, cfg in THREADS.items():
                db_path = self.base_dir / cfg["db_file"]
                if db_path.exists():
                    try:
                        conn = sqlite3.connect(str(db_path))
                        conn.row_factory = sqlite3.Row
                        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
                        conn.close()
                        if row:
                            m = re.search(r"page-(\d+)", row["source_page"] or "")
                            p_num = int(m.group(1)) if m else 1
                            video = self.register_video(dict(row), p_num, thread_key=t_key)
                            break
                    except Exception as e:
                        logger.debug("Error checking video in %s: %s", db_path.name, e)

        if not video:
            return None, None, None, [], []

        all_videos = list(self.id_to_video.values())
        related_videos = [v for v in all_videos if v["id"] != video_id and v.get("username") == video.get("username")]
        if len(related_videos) < 10:
            extra = [v for v in all_videos if v["id"] != video_id and v not in related_videos][:10 - len(related_videos)]
            related_videos.extend(extra)

        recommended_videos = [v for v in all_videos if v["id"] != video_id and v not in related_videos][:10]

        sorted_ids = sorted(self.id_to_video.keys())
        cur_idx = sorted_ids.index(video_id) if video_id in sorted_ids else -1
        prev_video = self.id_to_video.get(sorted_ids[cur_idx - 1]) if cur_idx > 0 else None
        next_video = self.id_to_video.get(sorted_ids[cur_idx + 1]) if 0 <= cur_idx < len(sorted_ids) - 1 else None

        return video, prev_video, next_video, related_videos, recommended_videos

    def search_videos(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Instant search suggestions across all videos in memory."""
        q = (query or "").strip().lower()
        if not q:
            return []

        all_v = list(self.id_to_video.values())
        return [
            v for v in all_v
            if q in (v.get("display_title") or "").lower()
            or q in (v.get("username") or "").lower()
            or q in str(v.get("id"))
        ][:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime global statistics for template context."""
        return {
            "total": len(self.id_to_video),
            "is_live": self.is_live_mode,
            "last_error": self.last_scrape_error,
            "threads": THREADS,
            "active_thread": self.active_thread,
        }


# Global service instance
video_service = VideoService()
