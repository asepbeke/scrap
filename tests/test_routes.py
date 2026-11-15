"""Integration tests for Web and API endpoints."""

import unittest
from unittest.mock import patch
from tests.conftest import get_test_app
from app.services.video_service import video_service


class RouteTestCase(unittest.TestCase):
    """Test suite for HTTP routing and API contracts."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_test_app()
        cls.client = cls.app.test_client()

    @patch("app.services.video_service.scrape_live_page")
    def test_index_route(self, mock_scrape):
        """Test homepage rendering with mocked live scraper."""
        mock_scrape.return_value = {
            "videos": [],
            "current_page": 741,
            "latest_page": 741,
            "thread_title": "Test Live Show Title",
            "base_url": "https://www.semprot.com/threads/1502373",
            "page_url": "https://www.semprot.com/threads/1502373/page-741",
            "thread_key": "live_show",
            "thread_name": "Konten Live Show (Part 3)",
        }
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("StreamVault", content)

    @patch("app.services.video_service.scrape_live_page")
    def test_index_with_thread_params(self, mock_scrape):
        """Test thread switching via query parameters."""
        mock_scrape.return_value = {
            "videos": [],
            "current_page": 100,
            "latest_page": 100,
            "thread_title": "Test Title",
            "base_url": "https://www.semprot.com/threads/test",
            "page_url": "https://www.semprot.com/threads/test/page-100",
            "thread_key": "live_show",
            "thread_name": "Test Name",
        }
        for t_key in ["live_show", "igo", "req_live"]:
            response = self.client.get(f"/?thread={t_key}")
            self.assertEqual(response.status_code, 200)

    def test_api_threads(self):
        """Test /api/threads contract."""
        response = self.client.get("/api/threads")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("threads", data)
        self.assertIn("live_show", data["threads"])

    def test_api_videos(self):
        """Test /api/videos pagination and filtering."""
        response = self.client.get("/api/videos?limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["videos"], list)

    def test_api_search(self):
        """Test /api/search instant search endpoint."""
        response = self.client.get("/api/search?q=test")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["results"], list)

    def test_watch_page_or_404(self):
        """Test watch page with known or unknown video ID."""
        if video_service.id_to_video:
            first_id = list(video_service.id_to_video.keys())[0]
            response = self.client.get(f"/watch/{first_id}")
            self.assertEqual(response.status_code, 200)

        # Non-existent video should return 404
        response_404 = self.client.get("/watch/99999999")
        self.assertEqual(response_404.status_code, 404)


if __name__ == "__main__":
    unittest.main()
