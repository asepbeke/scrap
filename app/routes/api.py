"""REST API endpoints for videos, instant search, threads, and live scraping."""

from flask import Blueprint, jsonify, request
from config import THREADS
from app.services.video_service import video_service
from app.services.scraper_service import scrape_live_page
from app.models.video import save_videos_to_db

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/videos")
def api_videos():
    """Return paginated, filtered and sorted videos as JSON."""
    thread = request.args.get("thread", "live_show").strip().lower()
    provider = request.args.get("provider", "").strip().lower()
    q = request.args.get("q", "").strip().lower()
    limit = request.args.get("limit", 24, type=int)
    offset = request.args.get("offset", 0, type=int)
    sort_order = request.args.get("sort", "newest")

    all_v = list(video_service.id_to_video.values())
    if thread:
        all_v = [v for v in all_v if v.get("thread_key") == thread]
    if provider:
        all_v = [v for v in all_v if provider in (v.get("provider") or "").lower()]
    if q:
        all_v = [
            v for v in all_v
            if q in (v.get("display_title") or "").lower()
            or q in (v.get("username") or "").lower()
        ]

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
        "videos": slice_v,
    })


@api_bp.route("/video/<int:video_id>")
def api_video_detail(video_id: int):
    """Return specific video details, next, prev, and related videos as JSON."""
    video, prev_vid, next_vid, related, _ = video_service.get_video_detail(video_id)
    if not video:
        return jsonify({"status": "error", "message": "Video not found"}), 404

    return jsonify({
        "status": "success",
        "video": video,
        "related": related,
        "prev_video": prev_vid,
        "next_video": next_vid,
    })


@api_bp.route("/threads")
def api_threads():
    """Return available threads list and current latest known pages."""
    return jsonify({
        "status": "success",
        "threads": THREADS,
        "active_thread": video_service.active_thread,
        "latest_pages": video_service.thread_latest,
    })


@api_bp.route("/search")
def api_search():
    """Instant search endpoint for quick preview suggestions."""
    q = request.args.get("q", "").strip().lower()
    matches = video_service.search_videos(q, limit=10)
    return jsonify({
        "status": "success",
        "query": q,
        "results": matches,
    })


@api_bp.route("/scrape")
def api_scrape():
    """Trigger live scrape via Playwright CDP and return JSON response."""
    req_thread = request.args.get("thread", "live_show").strip().lower()
    if req_thread not in THREADS:
        req_thread = "live_show"
    req_page = request.args.get("page", type=int)
    force = request.args.get("refresh", "0") == "1"
    cache_key = f"{req_thread}:{req_page}"

    if not force and req_page and cache_key in video_service.page_cache:
        return jsonify({
            "status": "cached",
            "thread": req_thread,
            "page": req_page,
            "videos": video_service.page_cache[cache_key],
        })

    try:
        data = scrape_live_page(target_page_num=req_page, thread_key=req_thread)
        v_list = []
        for item in data["videos"]:
            reg = video_service.register_video(item, data["current_page"], thread_key=req_thread)
            if reg:
                v_list.append(reg)

        if v_list:
            video_service.page_cache[f"{req_thread}:{data['current_page']}"] = v_list
            save_videos_to_db(v_list, thread_key=req_thread, base_dir=video_service.base_dir)

        return jsonify({
            "status": "live",
            "thread": req_thread,
            "page": data["current_page"],
            "latest_page": data["latest_page"],
            "videos": v_list,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "thread": req_thread,
            "error": str(e),
        }), 500
