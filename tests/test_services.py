"""Unit tests for services, models, and utility functions."""

import unittest
from app.utils.embed import format_embed_url
from app.utils.helpers import extract_v_page, hero_rank_key, safe_int
from app.services.scraper_service import get_base_thread_url, is_video_link, extract_videos_from_html
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



    def test_dom_proximity_pairing_interleaved(self):
        """Test that videos for Model A get Model A's image, and Model B get Model B's image."""
        sample_html = '''
        <div class="message" id="post-101">
            <div class="message-name"><span class="username">MasterUploader</span></div>
            <div class="message-body">
                <div class="bbWrapper">
                    Model Lauramana<br>
                    <img src="https://example.com/lauramana.jpg" class="bbImage"><br>
                    <a href="https://vidara.to/v/laura1">Link Laura 1</a><br>
                    <a href="https://vidara.to/v/laura2">Link Laura 2</a><br>
                    <br>
                    Model Sherly<br>
                    <img src="https://example.com/sherly.jpg" class="bbImage"><br>
                    <a href="https://vidara.to/v/sherly1">Link Sherly 1</a><br>
                    <a href="https://vidara.to/v/sherly2">Link Sherly 2</a>
                </div>
            </div>
        </div>
        '''
        results = extract_videos_from_html(sample_html, "https://example.com/page-1")
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["video_url"], "https://vidara.to/v/laura1")
        self.assertEqual(results[0]["image_url"], "https://example.com/lauramana.jpg")
        self.assertEqual(results[1]["video_url"], "https://vidara.to/v/laura2")
        self.assertEqual(results[1]["image_url"], "https://example.com/lauramana.jpg")
        self.assertEqual(results[2]["video_url"], "https://vidara.to/v/sherly1")
        self.assertEqual(results[2]["image_url"], "https://example.com/sherly.jpg")
        self.assertEqual(results[3]["video_url"], "https://vidara.to/v/sherly2")
        self.assertEqual(results[3]["image_url"], "https://example.com/sherly.jpg")

    def test_dom_proximity_pairing_batch_and_smilies(self):
        """Test that batch images pair 1:1 with batch videos, and smilies/quotes are ignored."""
        sample_html = '''
        <div class="message" id="post-102">
            <div class="message-name"><span class="username">Zupazup</span></div>
            <div class="message-body">
                <div class="bbWrapper">
                    <blockquote class="bbCodeBlock--quote">
                        Quoted User said:<br>
                        <img src="https://example.com/old_quote.jpg">
                        <a href="https://vidara.to/v/old_quoted_vid">Old Link</a>
                    </blockquote>
                    <img src="https://example.com/smilies/fire.gif" class="smilie"> Halo suhu:<br>
                    <img src="https://example.com/pic1.jpg" class="bbImage">
                    <img src="https://example.com/pic2.jpg" class="bbImage">
                    <br>
                    <a href="https://vidara.to/v/new_vid1">Vid 1</a><br>
                    <a href="https://vidara.to/v/new_vid2">Vid 2</a>
                </div>
            </div>
        </div>
        '''
        results = extract_videos_from_html(sample_html, "https://example.com/page-1")
        self.assertEqual(len(results), 2)
        # Quoted vid must not be extracted
        urls = [r["video_url"] for r in results]
        self.assertNotIn("https://vidara.to/v/old_quoted_vid", urls)
        # Smilie must not contaminate image_url
        self.assertEqual(results[0]["image_url"], "https://example.com/pic1.jpg")
        self.assertEqual(results[0]["video_url"], "https://vidara.to/v/new_vid1")
        self.assertEqual(results[1]["image_url"], "https://example.com/pic2.jpg")
        self.assertEqual(results[1]["video_url"], "https://vidara.to/v/new_vid2")


if __name__ == "__main__":

    unittest.main()
