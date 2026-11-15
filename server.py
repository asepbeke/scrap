"""Backward compatibility wrapper for server.py.

Delegates execution to the refactored modular Flask application factory.
Maintains compatibility with legacy batch files (e.g. run_web.bat) and test scripts.
"""

import os
from app import create_app
from app.services.video_service import video_service
from config import THREADS

# Expose app and shared variables for backward compatibility
app = create_app(os.getenv("FLASK_ENV", "development"))
ID_TO_VIDEO = video_service.id_to_video
URL_TO_ID = video_service.url_to_id
PAGE_CACHE = video_service.page_cache
THREAD_LATEST = video_service.thread_latest
THREAD_TITLES = video_service.thread_titles

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    print("==================================================")
    print("   StreamVault CINEMATIC Realtime Streaming Server")
    print(f"   URL: http://127.0.0.1:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=debug)
