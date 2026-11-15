"""Test configuration and fixtures for unittest and pytest."""

import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.services.video_service import video_service


def get_test_app():
    """Create a configured Flask test application."""
    os.environ["FLASK_ENV"] = "testing"
    test_app = create_app("testing")
    test_app.config["TESTING"] = True
    return test_app
