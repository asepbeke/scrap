"""StreamVault Flask Application Factory.

Instantiates and configures the Flask application, registers blueprints,
configures logging, context processors, and error handlers.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request, url_for

from config import config_by_name, Config
from app.routes.web import web_bp
from app.routes.api import api_bp
from app.services.video_service import video_service


def configure_logging(app: Flask) -> None:
    """Configure structured logging for console and file output."""
    logs_dir = Path(app.config.get("LOGS_DIR", Config.LOGS_DIR))
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s in %(filename)s:%(lineno)d: %(message)s"
    formatter = logging.Formatter(log_format)

    # File Handler
    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Root Logger Config
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Avoid duplicate handlers if create_app called multiple times (e.g. testing)
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)


def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers for 404 and 500."""

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Resource not found"}), 404
        return render_template("index.html", **video_service.get_page_data()), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("Internal Server Error: %s", error)
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Internal server error"}), 500
        return render_template("index.html", **video_service.get_page_data()), 500


def create_app(config_name: Optional[str] = None) -> Flask:
    """Application factory for StreamVault Flask application."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    cfg_class = config_by_name.get(config_name, config_by_name["default"])

    app = Flask(
        __name__,
        template_folder=str(cfg_class.TEMPLATES_DIR),
        static_folder=str(cfg_class.STATIC_DIR)
    )
    app.config.from_object(cfg_class)

    # Setup Logging
    configure_logging(app)
    app.logger.info("Initializing StreamVault with config: %s", config_name)

    # Register Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # Context Processors
    @app.context_processor
    def inject_global_stats():
        return {"stats": video_service.get_stats()}

    # Backward Compatibility for url_for without blueprint prefix ('index' -> 'web.index')
    def handle_url_build_error(error, endpoint, values):
        if endpoint in ("index", "watch"):
            return url_for(f"web.{endpoint}", **values)
        if endpoint.startswith("api_"):
            clean_ep = endpoint.replace("api_", "")
            return url_for(f"api.{clean_ep}", **values)
        raise error

    app.url_build_error_handlers.append(handle_url_build_error)

    # Error Handlers
    register_error_handlers(app)

    # Preload initial video pool from SQLite databases
    video_service.preload_all_threads(limit=300)

    return app
