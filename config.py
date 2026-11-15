"""Centralized configuration for the StreamVault Video Streaming Application.

Defines environment-based configurations, directory paths, supported video hosts,
and thread metadata.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Target Forum Threads Configuration
THREADS = {
    "live_show": {
        "id": "live_show",
        "name": "Konten Live Show (Part 3)",
        "thread_id": "1502373",
        "base_url": "https://www.semprot.com/threads/konten-live-show-disini-dilarang-request-ask-bertanya-part-3-bukan-tempat-reques-dan-bertanya-spam-oot-dilarang.1502373",
        "default_page": 741,
        "db_file": "videos.db",
        "csv_file": "videos.csv",
        "icon": "fa-fire",
        "badge_color": "bg-red-600"
    },
    "igo": {
        "id": "igo",
        "name": "Request Film IGO (Part 9)",
        "thread_id": "1575354",
        "base_url": "https://www.semprot.com/threads/request-film-igo-di-sini-dilarang-rekuest-video-di-bawah-umur-part-9.1575354",
        "default_page": 3016,
        "db_file": "videos_igo.db",
        "csv_file": "videos_igo.csv",
        "icon": "fa-film",
        "badge_color": "bg-pink-600"
    },
    "req_live": {
        "id": "req_live",
        "name": "Request & Ask Live Show",
        "thread_id": "1502696",
        "base_url": "https://www.semprot.com/threads/request-ask-video-live-show-disini-dilarang-share-tanpa-ada-yang-request.1502696",
        "default_page": 1625,
        "db_file": "videos_req_live.db",
        "csv_file": "videos_req_live.csv",
        "icon": "fa-comments",
        "badge_color": "bg-amber-600"
    }
}

# Supported Video Hosts and Domain Keywords
VIDEO_HOSTS = {
    "dood.to",
    "dood.so",
    "dood.wf",
    "dood.cx",
    "dood.la",
    "dood.ws",
    "dood.sh",
    "dood.re",
    "dood.video",
    "doodstream.com",
    "ds2play.com",
    "doodstream.co",
    "doods.pro",
    "vidara.to",
    "vidara.so",
    "vidara.org",
    "playmogo.com",
    "streamwish.to",
    "streamwish.com",
    "filelions.to",
    "luluvdo.com",
}

VIDEO_KEYWORDS = [
    "dood", "vidara", "playmogo", "streamwish", "filelions",
    "luluvdo", "streamtape", "mp4upload"
]


class Config:
    """Base Configuration class."""

    SECRET_KEY = os.getenv("SECRET_KEY", "streamvault-dev-secret-key-2026")
    DEBUG = False
    TESTING = False
    PORT = int(os.getenv("PORT", 5000))

    # Path Settings using pathlib
    BASE_DIR = BASE_DIR
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"
    THUMB_DIR = STATIC_DIR / "thumbnails"
    LOGS_DIR = BASE_DIR / "logs"

    # Playwright Chrome DevTools Protocol Settings
    CDP_HOST = os.getenv("CDP_HOST", "127.0.0.1")
    CDP_PORT = int(os.getenv("CDP_PORT", 9222))
    CDP_TIMEOUT = int(os.getenv("CDP_TIMEOUT", 5000))

    # Scraper Throttling
    SCRAPER_DELAY_MS = int(os.getenv("SCRAPER_DELAY_MS", 2000))

    # Thread Settings
    DEFAULT_THREAD = os.getenv("DEFAULT_THREAD", "live_show")
    THREADS = THREADS
    VIDEO_HOSTS = VIDEO_HOSTS
    VIDEO_KEYWORDS = VIDEO_KEYWORDS


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    CDP_TIMEOUT = 1000


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
