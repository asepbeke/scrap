"""Web HTML views and routes for the video gallery and player."""

from flask import Blueprint, abort, render_template, request
from config import THREADS
from app.services.video_service import video_service

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """Main Video Streaming Gallery page.

    Handles real-time scraping, thread switching, filtering, sorting, and pagination.
    """
    req_thread = request.args.get("thread", "live_show").strip().lower()
    req_page = request.args.get("page", type=int)
    force_refresh = request.args.get("refresh", "0") == "1"
    provider_filter = request.args.get("provider", "").strip().lower()
    uploader_filter = request.args.get("uploader", "").strip().lower()
    q_search = request.args.get("q", "").strip().lower()
    sort_order = request.args.get("sort", "newest").strip()

    page_data = video_service.get_page_data(
        thread_key=req_thread,
        page_num=req_page,
        force_refresh=force_refresh,
        provider_filter=provider_filter,
        uploader_filter=uploader_filter,
        q_search=q_search,
        sort_order=sort_order,
    )

    return render_template("index.html", **page_data)


@web_bp.route("/watch/<int:video_id>")
def watch(video_id: int):
    """Video Detail & Cinema Player page.

    Includes iframe/direct player, recommended videos, and playlist navigation.
    """
    video, prev_vid, next_vid, related, recommended = video_service.get_video_detail(video_id)
    if not video:
        abort(404)

    return render_template(
        "watch.html",
        video=video,
        prev_video=prev_vid,
        next_video=next_vid,
        related_videos=related,
        recommended_videos=recommended,
        active_thread=video.get("thread_key", "live_show"),
        threads=THREADS,
    )
