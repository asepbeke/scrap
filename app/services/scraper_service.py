"""Playwright CDP Scraper Service for Realtime Forum Page Extraction.

Connects to a running Chrome instance via Remote Debugging Protocol (port 9222)
to extract forum posts, video links, thumbnails, and pagination numbers.
"""

import logging
import re
import socket
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional
from playwright.sync_api import sync_playwright

from config import THREADS, VIDEO_HOSTS, VIDEO_KEYWORDS

logger = logging.getLogger(__name__)


def is_video_link(url: str) -> bool:
    """Validate whether an anchor href points to a supported streaming video host."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.lower()
        if not host:
            return False

        # Direct media files
        if path.endswith((".mp4", ".webm", ".mkv", ".mov")):
            return True

        # Supported video streaming providers
        if host in VIDEO_HOSTS or any(k in host for k in VIDEO_KEYWORDS):
            return (
                path.startswith(("/e/", "/d/", "/v/"))
                or bool(re.search(r"/[a-zA-Z0-9_-]{5,}", path))
            )

        return False
    except Exception:
        return False


def get_base_thread_url(url: str) -> str:
    """Extract clean thread base URL, removing any /page-XXXX repetitions."""
    if not url:
        return ""

    m = re.match(r"^(https?://[^/]+/threads/[^/]+)", url)
    if m:
        base = m.group(1).rstrip("/")
        base = re.sub(r"(/page-\d+)+$", "", base)
        return base

    parsed = urlparse(url)
    clean_path = re.sub(r"(/page-\d+)+/?$", "", parsed.path).rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{clean_path}"


def get_latest_page_number(page) -> int:
    """Discover the highest page number available on the forum page."""
    page_numbers = []
    try:
        nav_elements = page.locator(".pageNav-page, .pageNav-jump, .pageNavSimple-el")
        count = nav_elements.count()
        for i in range(count):
            try:
                el = nav_elements.nth(i)
                text = el.inner_text().strip().replace(",", "").replace(".", "")
                if text.isdigit():
                    page_numbers.append(int(text))
                href = el.get_attribute("href") or ""
                match = re.search(r"page-(\d+)", href)
                if match:
                    page_numbers.append(int(match.group(1)))
            except Exception:
                continue
    except Exception as e:
        logger.debug("Error checking pageNav elements: %s", e)

    try:
        title_match = re.search(r"Page\s+(\d+)", page.title(), re.IGNORECASE)
        if title_match:
            page_numbers.append(int(title_match.group(1)))
    except Exception:
        pass

    try:
        url_match = re.search(r"page-(\d+)", page.url, re.IGNORECASE)
        if url_match:
            page_numbers.append(int(url_match.group(1)))
    except Exception:
        pass

    return max(page_numbers) if page_numbers else 1


def extract_videos_from_page(page) -> List[Dict[str, Any]]:
    """Extract post metadata, image thumbnails, and video URLs from a thread page."""
    results = []
    posts = page.locator(".message")
    total_posts = posts.count()

    for i in range(total_posts):
        post = posts.nth(i)
        post_id = post.get_attribute("id") or f"post-{i+1}"

        # Username extraction
        username_elem = post.locator(".message-name .username, .username").first
        username = username_elem.inner_text().strip() if username_elem.count() else "Unknown"

        # Post title extraction
        title_elem = post.locator(".message-subject, .post-title, h1, h2").first
        post_title = title_elem.inner_text().strip() if title_elem.count() else ""

        # Content block and image attachments
        content = post.locator(".bbWrapper")
        if not content.count():
            continue

        images = content.locator("img")
        img_urls = []
        for img_idx in range(images.count()):
            img_tag = images.nth(img_idx)
            src = (
                img_tag.get_attribute("src")
                or img_tag.get_attribute("data-src")
                or img_tag.get_attribute("data-url")
                or ""
            )
            if src and not src.startswith("data:"):
                img_urls.append(src)

        anchors = content.locator("a[href]")
        video_idx = 0
        for j in range(anchors.count()):
            anchor = anchors.nth(j)
            url = anchor.get_attribute("href")
            if not url or not url.startswith("http"):
                continue

            if is_video_link(url):
                matched_img = (
                    img_urls[video_idx]
                    if video_idx < len(img_urls)
                    else (img_urls[0] if img_urls else "")
                )
                video_idx += 1

                results.append({
                    "post_id": post_id,
                    "username": username,
                    "post_title": post_title,
                    "image_url": matched_img,
                    "video_url": url,
                    "provider": urlparse(url).hostname or "",
                    "link_name": anchor.inner_text().strip(),
                    "source_page": page.url
                })

    # Deduplicate by video_url on this page
    unique = {}
    for item in results:
        unique[item["video_url"]] = item
    return list(unique.values())


def is_cdp_ready(host: str = "127.0.0.1", port: int = 9222, timeout: float = 0.8) -> bool:
    """Check if the Chrome DevTools Protocol port is open and accepting socket connections."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def scrape_live_page(target_page_num: Optional[int] = None, thread_key: str = "live_show") -> Dict[str, Any]:
    """Execute live synchronous scraping via Playwright CDP on Chrome port 9222."""
    if not is_cdp_ready():
        raise ConnectionError(
            "Tidak dapat terhubung ke Chrome pada port 9222. "
            "Pastikan Google Chrome telah dibuka dengan: --remote-debugging-port=9222"
        )

    thread_info = THREADS.get(thread_key, THREADS["live_show"])
    target_thread_id = thread_info["thread_id"]
    default_base_url = thread_info["base_url"]
    default_page_num = thread_info["default_page"]

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
        except Exception as e:
            raise ConnectionError(
                "Tidak dapat terhubung ke Chrome pada port 9222. "
                "Pastikan Google Chrome telah dibuka dengan: --remote-debugging-port=9222"
            ) from e

        context = browser.contexts[0]

        # 1. Search for tab specific to target thread
        tab = next(
            (t for t in context.pages if target_thread_id in t.url and "Log in" not in t.title()),
            None
        )

        # 2. Search for any forum tab
        if tab is None:
            tab = next(
                (t for t in context.pages if ("/threads/" in t.url or "semprot.com" in t.url) and "Log in" not in t.title()),
                None
            )

        # 3. Fallback to first tab or create new tab
        if tab is None:
            tab = context.pages[0] if context.pages else context.new_page()

        clean_tab_base = get_base_thread_url(tab.url)
        needs_initial_nav = (
            target_thread_id not in tab.url
            or not clean_tab_base
            or target_thread_id not in clean_tab_base
            or "Oops!" in tab.title()
        )

        if needs_initial_nav:
            p_to_open = target_page_num or default_page_num
            initial_target_url = f"{default_base_url}/page-{p_to_open}"
            tab.goto(initial_target_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(800)
            base_url = default_base_url
        else:
            base_url = clean_tab_base

        latest_page = max(get_latest_page_number(tab), default_page_num)

        if target_page_num is None:
            m_curr = re.search(r"page-(\d+)", tab.url)
            current_page_num = int(m_curr.group(1)) if m_curr else latest_page
        else:
            current_page_num = int(target_page_num)

        target_url = f"{base_url}/page-{current_page_num}"

        clean_current_tab_url = tab.url.split("?")[0].split("#")[0].rstrip("/")
        if clean_current_tab_url != target_url.rstrip("/") or "Oops!" in tab.title():
            tab.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(800)
            latest_page = max(get_latest_page_number(tab), latest_page, current_page_num)

        videos = extract_videos_from_page(tab)
        thread_title = tab.title()

        return {
            "videos": videos,
            "current_page": current_page_num,
            "latest_page": latest_page,
            "thread_title": thread_title,
            "base_url": base_url,
            "page_url": tab.url,
            "thread_key": thread_key,
            "thread_name": thread_info["name"]
        }
