import os
import re
import sqlite3
import time
import hashlib
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, abort, send_from_directory, Response, redirect
from scraper import scrape_live_page, THREADS

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "videos.db")
THUMB_DIR = os.path.join(BASE_DIR, "static", "thumbnails")

# In-Memory Video Store & Page Cache for Realtime Scraping
URL_TO_ID = {}
ID_TO_VIDEO = {}
PAGE_CACHE = {}
THREAD_LATEST = {
    "live_show": 741,
    "igo": 3016,
    "req_live": 1625
}
THREAD_TITLES = {
    "live_show": "Konten Live Show (Part 3)",
    "igo": "Request Film IGO (Part 9)",
    "req_live": "Request & Ask Live Show"
}
# Safely construct thread base URLs, handling missing keys gracefully
THREAD_BASE_URLS = {
    "live_show": THREADS.get("live_show", {}).get("base_url", ""),
    "igo":       THREADS.get("igo",       {}).get("base_url", ""),
    "req_live":  THREADS.get("req_live",  {}).get("base_url", "")
}

ACTIVE_THREAD = "live_show"
IS_LIVE_MODE = False
LAST_SCRAPE_ERROR = ""
NEXT_ID = 1


def save_videos_to_db(videos, thread_key="live_show"):
    """Auto-upsert scraped videos into SQLite so database fallback is always fresh"""
    if not videos:
        return
    cfg = THREADS.get(thread_key, THREADS["live_show"])
    db_path = os.path.join(BASE_DIR, cfg["db_file"])
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('''
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
        ''')
        for item in videos:
            v_url = (item.get("video_url") or "").strip()
            if not v_url:
                continue
            conn.execute('''
                INSERT INTO videos (post_id, username, post_title, image_url, video_url, provider, link_name, source_page, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(video_url) DO UPDATE SET
                    post_title = CASE WHEN excluded.post_title != '' THEN excluded.post_title ELSE videos.post_title END,
                    image_url = CASE WHEN excluded.image_url != '' THEN excluded.image_url ELSE videos.image_url END,
                    source_page = CASE WHEN excluded.source_page != '' THEN excluded.source_page ELSE videos.source_page END
            ''', (
                item.get("post_id", ""),
                item.get("username", "Unknown"),
                item.get("post_title", ""),
                item.get("image_url", "") or item.get("thumbnail_url", ""),
                v_url,
                item.get("provider", ""),
                item.get("link_name", ""),
                item.get("source_page", "")
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Save Notice]: {e}")


def format_embed_url(video_url, provider):
    if not video_url:
        return ""
    video_url = video_url.strip()
    provider = (provider or "").lower()

    # Dood & Playmogo embedding (/d/ -> /e/)
    if any(k in provider or k in video_url for k in ["dood", "playmogo"]):
        if "/d/" in video_url:
            return re.sub(r"/d/", "/e/", video_url)
        return video_url

    # Vidara embedding (/v/<id> -> /e/<id>)
    if "vidara" in provider or "vidara" in video_url:
        m = re.search(r"/(?:v|e)/([a-zA-Z0-9]+)", video_url)
        if m:
            v_id = m.group(1)
            parsed = urlparse(video_url)
            host = parsed.netloc or "vidara.to"
            scheme = parsed.scheme or "https"
            return f"{scheme}://{host}/e/{v_id}"
        return re.sub(r"/v/", "/e/", video_url)

    return video_url


def register_video(raw_item, page_num, thread_key="live_show"):
    global NEXT_ID
    url = raw_item.get("video_url", "").strip()
    if not url:
        return None

    db_id = raw_item.get("id")
    if db_id and isinstance(db_id, int):
        v_id = db_id
        URL_TO_ID[url] = v_id
        if v_id >= NEXT_ID:
            NEXT_ID = v_id + 1
    elif url in URL_TO_ID:
        v_id = URL_TO_ID[url]
    else:
        v_id = NEXT_ID
        URL_TO_ID[url] = v_id
        NEXT_ID += 1

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

    # Original webpage URL where the video was obtained (sourceUrl)
    source_page = (raw_item.get("source_page") or raw_item.get("sourceUrl") or raw_item.get("source_url") or "").strip()
    item["source_page"] = source_page
    item["source_url"] = source_page or url
    item["sourceUrl"] = item["source_url"]
    item["title"] = item["display_title"]
    item["category"] = THREADS.get(thread_key, {}).get("name", "Thread")
    item["forum_page"] = str(page_num)
    item["thread_key"] = thread_key
    item["thread_name"] = THREADS.get(thread_key, {}).get("name", "Thread")

    # Deterministic metadata for luxury streaming experience
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

    # Tag/genre approximation
    genres = ["Live Show", "Exclusive", "Popular", "Trending", "HD Studio"]
    item["genre"] = genres[h % len(genres)]

    ID_TO_VIDEO[v_id] = item
    return item


def preload_db_videos(limit=200, thread_key="live_show"):
    """Pre-populates memory with recent videos from SQLite for rich home sections"""
    cfg = THREADS.get(thread_key, THREADS["live_show"])
    db_path = os.path.join(BASE_DIR, cfg["db_file"])
    if not os.path.exists(db_path):
        return
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('''
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
        ''')
        rows = conn.execute("SELECT * FROM videos ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        for r in rows:
            m = re.search(r'page-(\\d+)', r["source_page"] or "")
            p_num = int(m.group(1)) if m else cfg["default_page"]
            register_video(dict(r), p_num, thread_key=thread_key)
        conn.close()
    except Exception as e:
        print(f"[Preload Notice]: {e}")


def get_videos_from_db_fallback(target_page_num=None, thread_key="live_show"):
    """Fallback ke database lokal sesuai thread jika Chrome CDP belum terhubung"""
    cfg = THREADS.get(thread_key, THREADS["live_show"])
    db_path = os.path.join(BASE_DIR, cfg["db_file"])
    def_page = cfg["default_page"]

    if not os.path.exists(db_path):
        return [], target_page_num or def_page, def_page, [def_page]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('''
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
    ''')

    # Cek daftar page yang ada di db
    p_rows = conn.execute("SELECT DISTINCT source_page FROM videos").fetchall()
    db_pages = []
    for r in p_rows:
        m = re.search(r'page-(\d+)', r[0] or "")
        if m:
            db_pages.append(int(m.group(1)))
    db_pages = sorted(list(set(db_pages)), reverse=True)
    latest_db_page = db_pages[0] if db_pages else def_page

    current_p = target_page_num if target_page_num else latest_db_page

    rows = conn.execute(
        "SELECT * FROM videos WHERE source_page LIKE ? ORDER BY id DESC",
        (f"%page-{current_p}%",)
    ).fetchall()

    if not rows:
        rows = conn.execute("SELECT * FROM videos ORDER BY id DESC LIMIT 50").fetchall()

    items = []
    for r in rows:
        v = register_video(dict(r), current_p, thread_key=thread_key)
        if v:
            items.append(v)

    conn.close()
    return items, current_p, latest_db_page, db_pages or [def_page]

# Preload initial pool on startup for all threads
for t_key in THREADS:
    preload_db_videos(300, t_key)


@app.context_processor
def inject_global_stats():
    return {
        "stats": {
            "total": len(ID_TO_VIDEO),
            "is_live": IS_LIVE_MODE,
            "last_error": LAST_SCRAPE_ERROR,
            "threads": THREADS,
            "active_thread": ACTIVE_THREAD
        }
    }


@app.route("/")
def index():
    global IS_LIVE_MODE, LAST_SCRAPE_ERROR, ACTIVE_THREAD

    # Parameter query
    req_thread = request.args.get("thread", "live_show").strip().lower()
    if req_thread not in THREADS:
        req_thread = "live_show"
    ACTIVE_THREAD = req_thread
    curr_thread_cfg = THREADS[req_thread]

    req_page = request.args.get("page", type=int)
    force_refresh = request.args.get("refresh", "0") == "1"
    provider_filter = request.args.get("provider", "").strip().lower()
    uploader_filter = request.args.get("uploader", "").strip().lower()
    q_search = request.args.get("q", "").strip().lower()
    sort_order = request.args.get("sort", "newest").strip()

    cache_key = f"{req_thread}:{req_page}" if req_page else None
    latest_known = THREAD_LATEST.get(req_thread, curr_thread_cfg["default_page"])
    current_page_num = req_page or latest_known
    available_pages = []
    live_videos = []

    # 1. Cek Cache in-memory terlebih dahulu (kecuali force_refresh)
    if not force_refresh and cache_key and cache_key in PAGE_CACHE:
        live_videos = PAGE_CACHE[cache_key]
        current_page_num = req_page
        IS_LIVE_MODE = True
        LAST_SCRAPE_ERROR = ""
    else:
        # 2. Coba scrape realtime via Playwright CDP
        try:
            from scraper import scrape_live_page
            scrape_data = scrape_live_page(target_page_num=req_page, thread_key=req_thread)
            
            raw_videos = scrape_data["videos"]
            current_page_num = scrape_data["current_page"]
            latest_known = scrape_data["latest_page"]
            THREAD_LATEST[req_thread] = latest_known
            THREAD_TITLES[req_thread] = scrape_data["thread_title"]
            THREAD_BASE_URLS[req_thread] = scrape_data["base_url"]

            # Daftarkan video ke memori
            live_videos = []
            for item in raw_videos:
                reg_item = register_video(item, current_page_num, thread_key=req_thread)
                if reg_item:
                    live_videos.append(reg_item)

            if live_videos:
                PAGE_CACHE[f"{req_thread}:{current_page_num}"] = live_videos
                save_videos_to_db(live_videos, thread_key=req_thread)
                IS_LIVE_MODE = True
                LAST_SCRAPE_ERROR = ""
            else:
                # Scrape sukses tapi tidak menemukan video di halaman ini -> ambil dari DB cadangan
                db_vids, _, _, db_pages = get_videos_from_db_fallback(req_page, thread_key=req_thread)
                if db_vids:
                    live_videos = db_vids
                    available_pages = db_pages
                IS_LIVE_MODE = True
                LAST_SCRAPE_ERROR = f"Halaman {current_page_num} tidak memuat link video baru. Menampilkan data cadangan."
        except Exception as e:
            # Gagal koneksi CDP (misal Chrome belum dibuka) -> Fallback ke database
            IS_LIVE_MODE = False
            LAST_SCRAPE_ERROR = str(e)
            live_videos, current_page_num, latest_known, db_pages = get_videos_from_db_fallback(req_page, thread_key=req_thread)
            available_pages = db_pages

    # Hitung daftar navigasi halaman (termasuk jika user membuka Custom Page seperti 100 atau 3016)
    if not available_pages:
        if current_page_num >= latest_known - 8:
            start_p = max(1, latest_known - 9)
            available_pages = list(range(start_p, latest_known + 1))
        else:
            start_p = max(1, current_page_num - 4)
            end_p = min(latest_known, current_page_num + 4)
            available_pages = list(range(start_p, end_p + 1))
        available_pages.sort(reverse=True)

    # Preset Custom Page Milestones berdasarkan thread
    if req_thread == "igo":
        milestones = [1, 500, 1000, 1500, 2000, 2500, 3000, 3016]
    elif req_thread == "req_live":
        milestones = [1, 200, 500, 800, 1000, 1200, 1500, 1625]
    else:
        milestones = [1, 50, 100, 200, 300, 500, 700, 741]

    quick_milestones = [m for m in milestones if m < latest_known]
    if latest_known not in quick_milestones:
        quick_milestones.append(latest_known)

    # Filter lokal pada video di halaman yang sedang aktif
    filtered_videos = live_videos
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
            # Fallback search across all loaded videos for this thread
            all_known_for_thread = [v for v in ID_TO_VIDEO.values() if v.get("thread_key") == req_thread]
            filtered_videos = [
                v for v in all_known_for_thread
                if q_search in (v.get("display_title") or "").lower()
                or q_search in (v.get("username") or "").lower()
                or q_search in (v.get("post_id") or "").lower()
            ]

    # Sorting
    if sort_order == "oldest":
        filtered_videos = sorted(filtered_videos, key=lambda x: x["id"])
    elif sort_order == "random":
        import random
        filtered_videos = list(filtered_videos)
        random.shuffle(filtered_videos)
    elif sort_order == "popular":
        filtered_videos = sorted(filtered_videos, key=lambda x: x.get("views", "0"), reverse=True)
    else:
        filtered_videos = sorted(filtered_videos, key=lambda x: x["id"], reverse=True)

    # Hitung provider counts pada halaman aktif
    provider_counts = {}
    for v in live_videos:
        p = v.get("provider")
        if p:
            provider_counts[p] = provider_counts.get(p, 0) + 1

    # Helper to extract integer page number safely from video item
    def extract_v_page(v):
        fp = v.get("forum_page")
        if fp:
            try:
                return int(fp)
            except (ValueError, TypeError):
                pass
        m = re.search(r'page-(\\d+)', v.get("source_page") or "")
        if m:
            return int(m.group(1))
        return 0

    # 1. Filter videos for active thread first (with fallback to all known)
    all_known = list(ID_TO_VIDEO.values())
    thread_vids = [v for v in all_known if v.get("thread_key") == req_thread]
    if not thread_vids:
        thread_vids = all_known

    # 2. FEATURED HERO VIDEOS: Strictly newest video from the newest page!
    # Rank by: (page_number DESC, has_thumbnail DESC, video_id DESC)
    def hero_rank_key(v):
        page = extract_v_page(v)
        has_thumb = 1 if (v.get("thumbnail_url") and len(v["thumbnail_url"]) > 10 and "/placeholder" not in v["thumbnail_url"]) else 0
        vid_id = v.get("id", 0)
        return (page, has_thumb, vid_id)

    sorted_hero = sorted(thread_vids, key=hero_rank_key, reverse=True)
    featured_videos = sorted_hero[:6] if sorted_hero else all_known[:6]

    # 3. Valid thumbnail pool for secondary collections
    valid_thumb_videos = [v for v in thread_vids if v.get("thumbnail_url") and len(v["thumbnail_url"]) > 10]
    if not valid_thumb_videos:
        valid_thumb_videos = thread_vids

    # Trending Now (Top 10 sorted by popularity/views)
    trending_videos = sorted(valid_thumb_videos, key=lambda x: x.get("views", "0"), reverse=True)[:10]

    # Recently Added (Strictly newest videos from latest pages)
    recent_videos = sorted(valid_thumb_videos, key=lambda v: (extract_v_page(v), v.get("id", 0)), reverse=True)[:12]

    # Recommended for You
    recommended_videos = [v for v in valid_thumb_videos if v not in trending_videos[:5]][:12]
    if not recommended_videos:
        recommended_videos = valid_thumb_videos[:10]

    # Most Popular
    popular_videos = sorted(valid_thumb_videos, key=lambda x: x.get("views", "0"), reverse=True)[:12]

    return render_template(
        "index.html",
        videos=filtered_videos,
        total_count=len(filtered_videos),
        current_forum_page=current_page_num,
        latest_page=latest_known,
        available_pages=available_pages,
        quick_milestones=quick_milestones,
        selected_provider=provider_filter,
        uploader=uploader_filter,
        q=q_search,
        sort=sort_order,
        provider_counts=provider_counts,
        is_live=IS_LIVE_MODE,
        last_error=LAST_SCRAPE_ERROR,
        thread_title=THREAD_TITLES.get(req_thread, curr_thread_cfg["name"]),
        active_thread=req_thread,
        threads=THREADS,
        current_thread_cfg=curr_thread_cfg,
        featured_videos=featured_videos,
        trending_videos=trending_videos,
        recommended_videos=recommended_videos,
        popular_videos=popular_videos,
        recent_videos=recent_videos
    )


@app.route("/watch/<int:video_id>")
def watch(video_id):
    video = ID_TO_VIDEO.get(video_id)
    if not video:
        # Coba cek di database SQLite yang sesuai jika belum di memory
        for db_file, t_key in [
            (DB_NAME, "live_show"), 
            (os.path.join(BASE_DIR, "videos_igo.db"), "igo"),
            (os.path.join(BASE_DIR, "videos_req_live.db"), "req_live")
        ]:
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
                conn.close()
                if row:
                    m = re.search(r'page-(\\d+)', row["source_page"] or "")
                    p_num = int(m.group(1)) if m else 1
                    video = register_video(dict(row), p_num, thread_key=t_key)
                    break

    if not video:
        abort(404)

    # Video lainnya yang sudah ada di memory
    all_videos = list(ID_TO_VIDEO.values())
    related_videos = [v for v in all_videos if v["id"] != video_id and v.get("username") == video.get("username")]
    if len(related_videos) < 10:
        extra = [v for v in all_videos if v["id"] != video_id and v not in related_videos][:10 - len(related_videos)]
        related_videos.extend(extra)

    # Recommended videos
    recommended_videos = [v for v in all_videos if v["id"] != video_id and v not in related_videos][:10]

    # Prev / Next
    sorted_ids = sorted(ID_TO_VIDEO.keys())
    cur_idx = sorted_ids.index(video_id) if video_id in sorted_ids else -1
    prev_video = ID_TO_VIDEO.get(sorted_ids[cur_idx - 1]) if cur_idx > 0 else None
    next_video = ID_TO_VIDEO.get(sorted_ids[cur_idx + 1]) if 0 <= cur_idx < len(sorted_ids) - 1 else None

    return render_template(
        "watch.html",
        video=video,
        prev_video=prev_video,
        next_video=next_video,
        related_videos=related_videos,
        recommended_videos=recommended_videos,
        active_thread=video.get("thread_key", "live_show"),
        threads=THREADS
    )


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.route("/api/videos")
def api_videos():
    """Returns paginated, filtered and sorted videos as JSON"""
    thread = request.args.get("thread", "live_show").strip().lower()
    page = request.args.get("page", type=int)
    provider = request.args.get("provider", "").strip().lower()
    q = request.args.get("q", "").strip().lower()
    limit = request.args.get("limit", 24, type=int)
    offset = request.args.get("offset", 0, type=int)
    sort_order = request.args.get("sort", "newest")

    all_v = list(ID_TO_VIDEO.values())
    if thread:
        all_v = [v for v in all_v if v.get("thread_key") == thread]
    if provider:
        all_v = [v for v in all_v if provider in (v.get("provider") or "").lower()]
    if q:
        all_v = [v for v in all_v if q in (v.get("display_title") or "").lower() or q in (v.get("username") or "").lower()]

    if sort_order == "oldest":
        all_v = sorted(all_v, key=lambda x: x["id"])
    elif sort_order == "popular":
        all_v = sorted(all_v, key=lambda x: x.get("views", "0"), reverse=True)
    else:
        all_v = sorted(all_v, key=lambda x: x["id"], reverse=True)

    total = len(all_v)
    slice_v = all_v[offset:offset + limit]

    return jsonify({
        "status": "success",
        "total": total,
        "offset": offset,
        "limit": limit,
        "videos": slice_v
    })


@app.route("/api/video/<int:video_id>")
def api_video_detail(video_id):
    """Returns specific video details, next, prev, and related videos"""
    video = ID_TO_VIDEO.get(video_id)
    if not video:
        for db_file, t_key in [
            (DB_NAME, "live_show"), 
            (os.path.join(BASE_DIR, "videos_igo.db"), "igo"),
            (os.path.join(BASE_DIR, "videos_req_live.db"), "req_live")
        ]:
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
                conn.close()
                if row:
                    m = re.search(r'page-(\\d+)', row["source_page"] or "")
                    p_num = int(m.group(1)) if m else 1
                    video = register_video(dict(row), p_num, thread_key=t_key)
                    break

    if not video:
        return jsonify({"status": "error", "message": "Video not found"}), 404

    all_videos = list(ID_TO_VIDEO.values())
    related = [v for v in all_videos if v["id"] != video_id and v.get("username") == video.get("username")][:8]
    if len(related) < 8:
        extra = [v for v in all_videos if v["id"] != video_id and v not in related][:8 - len(related)]
        related.extend(extra)

    sorted_ids = sorted(ID_TO_VIDEO.keys())
    cur_idx = sorted_ids.index(video_id) if video_id in sorted_ids else -1
    prev_video = ID_TO_VIDEO.get(sorted_ids[cur_idx - 1]) if cur_idx > 0 else None
    next_video = ID_TO_VIDEO.get(sorted_ids[cur_idx + 1]) if 0 <= cur_idx < len(sorted_ids) - 1 else None

    return jsonify({
        "status": "success",
        "video": video,
        "related": related,
        "prev_video": prev_video,
        "next_video": next_video
    })


@app.route("/api/threads")
def api_threads():
    """Returns available threads list and status"""
    return jsonify({
        "status": "success",
        "threads": THREADS,
        "active_thread": ACTIVE_THREAD,
        "latest_pages": THREAD_LATEST
    })


@app.route("/api/search")
def api_search():
    """Instant search endpoint for quick preview suggestions"""
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"status": "success", "results": []})

    all_v = list(ID_TO_VIDEO.values())
    matches = [
        v for v in all_v
        if q in (v.get("display_title") or "").lower()
        or q in (v.get("username") or "").lower()
        or q in str(v.get("id"))
    ][:10]

    return jsonify({
        "status": "success",
        "query": q,
        "results": matches
    })


@app.route("/api/scrape")
def api_scrape():
    """Trigger live scrape via Playwright CDP"""
    req_thread = request.args.get("thread", "live_show").strip().lower()
    if req_thread not in THREADS:
        req_thread = "live_show"
    req_page = request.args.get("page", type=int)
    force = request.args.get("refresh", "0") == "1"
    cache_key = f"{req_thread}:{req_page}"

    if not force and req_page and cache_key in PAGE_CACHE:
        return jsonify({
            "status": "cached",
            "thread": req_thread,
            "page": req_page,
            "videos": PAGE_CACHE[cache_key]
        })

    try:
        from scraper import scrape_live_page
        data = scrape_live_page(target_page_num=req_page, thread_key=req_thread)
        v_list = []
        for item in data["videos"]:
            reg = register_video(item, data["current_page"], thread_key=req_thread)
            if reg:
                v_list.append(reg)
        if v_list:
            PAGE_CACHE[f"{req_thread}:{data['current_page']}"] = v_list
            save_videos_to_db(v_list, thread_key=req_thread)
        return jsonify({
            "status": "live",
            "thread": req_thread,
            "page": data["current_page"],
            "latest_page": data["latest_page"],
            "videos": v_list
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "thread": req_thread,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f"   StreamVault CINEMATIC Realtime Streaming Server")
    print(f"   URL: http://127.0.0.1:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)
