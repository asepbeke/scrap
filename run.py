"""Application entry point for running the StreamVault Flask server."""

import os
from app import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    print("==================================================")
    print("   StreamVault CINEMATIC Realtime Streaming Server")
    print(f"   URL: http://127.0.0.1:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=debug)
