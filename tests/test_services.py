"""Unit tests for services, models, and utility functions."""

import unittest
from app.utils.embed import format_embed_url
from app.utils.helpers import extract_v_page, hero_rank_key, safe_int
from app.services.scraper_service import get_base_thread_url, is_video_link
from app.models.video import register_video_item


class ServicesTestCase(unittest.TestCase):
    """Unit tests for utility functions and business logic."""

    def test_format_embed_url_dood(self):
        """Test DoodStream embed conversion from /d/ to /e/."""
        url = "https://dood.to/d/sample123"
        embed = format_embed_url(url, "dood.to")
        self.assertEqual(embed, "https://dood.to/e/sample123")

    def test_format_embed_url_playmogo(self):
        """Test Playmogo embed conversion from /d/ to /e/."""
        url = "https://playmogo.com/d/sample456"
        embed = format_embed_url(url, "playmogo.com")
        self.assertEqual(embed, "https://playmogo.com/e/sample456")

    def test_format_embed_url_vidara(self):
        """Test Vidara embed conversion from /v/ to /e/."""
        url = "https://vidara.to/v/abc789xyz"
        embed = format_embed_url(url, "vidara.to")
        self.assertEqual(embed, "https://vidara.to/e/abc789xyz")

    def test_get_base_thread_url_clean(self):
        """Test that get_base_thread_url removes all repeating /page-XXX tokens."""
        corrupted = "https://www.semprot.com/threads/thread-title.1502373/page-741/page-738/page-740"
        clean = get_base_thread_url(corrupted)
        self.assertEqual(clean, "https://www.semprot.com/threads/thread-title.1502373")

    def test_is_video_link(self):
        """Test detection of valid video streaming links."""
        valid_links = [
            "https://vidara.to/v/r315T9hY3Gg40",
            "https://dood.to/e/zreewx0zidca",
            "https://playmogo.com/e/msj95opxnyau",
            "https://streamwish.to/e/abcdef",
            "https://example.com/video.mp4",
        ]
        invalid_links = [
            "https://www.imagebam.com/image/12345",
            "https://ibb.co/abcd",
            "https://www.semprot.com/threads/foo.123",
            "not-a-url",
        ]
        for v in valid_links:
            self.assertTrue(is_video_link(v), f"Expected True for {v}")
        for inv in invalid_links:
            self.assertFalse(is_video_link(inv), f"Expected False for {inv}")

    def test_helpers(self):
        """Test extract_v_page and safe_int helpers."""
        self.assertEqual(extract_v_page({"forum_page": "741"}), 741)
        self.assertEqual(extract_v_page({"source_page": "https://.../page-105"}), 105)
        self.assertEqual(extract_v_page({}), 0)
        self.assertEqual(safe_int("42", 0), 42)
        self.assertEqual(safe_int("invalid", 10), 10)

    def test_register_video_item(self):
        """Test in-memory video registration and deterministic metadata."""
        url_to_id = {}
        id_to_video = {}
        raw = {
            "video_url": "https://vidara.to/v/test12345",
            "post_title": "Test Title Video",
            "username": "tester",
            "image_url": "https://example.com/thumb.jpg",
        }
        item, next_id = register_video_item(raw, 741, "live_show", url_to_id, id_to_video, 1)
        self.assertIsNotNone(item)
        self.assertEqual(item["id"], 1)
        self.assertEqual(next_id, 2)
        self.assertIn("quality", item)
        self.assertIn("duration", item)
        self.assertIn("views", item)
        self.assertIn("rating", item)


if __name__ == "__main__":
    unittest.main()
