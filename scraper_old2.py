# Quick Optimization of scraper.py – minimal changes
# This version keeps the original synchronous Playwright flow but removes redundant calls
# and simplifies data‑extraction logic for a modest speed boost.

if __name__ == "__main__":
    import argparse, json, sys
    parser = argparse.ArgumentParser(description="Run quick scraper for a thread page")
    parser.add_argument("--page", type=int, help="Target page number (default: latest)")
    parser.add_argument("--thread", default="live_show", help="Thread key (default: live_show)")
    args = parser.parse_args()
    try:
        result = scrape_live_page(target_page_num=args.page, thread_key=args.thread)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

VIDEO_HOSTS = {"dood.to", "vidara.to", "vidara.so"}

THREADS = {
    "live_show": {
        "id": "live_show",
        "name": "Konten Live Show (Part 3)",
        "thread_id": "1502373",
        "base_url": "https://www.semprot.com/threads/konten-live-show-disini-dilarang-request-ask-bertanya-part-3-bukan-tempat-reques-dan-bertanya-spam-oot-dilarang.1502373",
        "default_page": 738,
        "db_file": "videos.db",
        "csv_file": "videos.csv",
        "icon": "fa-fire",
        "badge_color": "bg-red-600",
    },
    # ... other thread configs unchanged ...
}


def is_video_link(url: str) -> bool:
    """Return True if *url* points to a known video host and a valid path.
    The function catches all parsing errors and returns ``False`` safely.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.lower()
        if host not in VIDEO_HOSTS:
            return False
        if host == "dood.to":
            return path.startswith("/e/") or path.startswith("/d/")
        if host in {"vidara.to", "vidara.so"}:
            return path.startswith("/v/") or path.startswith("/e/")
        return False
    except Exception:
        return False


def get_base_thread_url(url: str) -> str:
    """Strip paging suffix from a thread URL, returning the base thread URL."""
    parsed = urlparse(url)
    clean_path = parsed.path.rstrip('/')
    base_path = re.sub(r"/page-\\d+$", "", clean_path)
    return f"{parsed.scheme}://{parsed.netloc}{base_path}"


def get_latest_page_number(page) -> int:
    """Inspect navigation elements to find the highest page number.
    The original implementation performed many ``.count()`` calls; here we cache the list.
    """
    page_numbers = []
    nav_elements = page.locator(".pageNav-page, .pageNav-jump, .pageNavSimple-el")
    count = nav_elements.count()
    for i in range(count):
        try:
            el = nav_elements.nth(i)
            text = el.inner_text().strip().replace(",", "").replace(".", "")
            if text.isdigit():
                page_numbers.append(int(text))
            href = el.get_attribute("href") or ""
            match = re.search(r"page-(\\d+)", href)
            if match:
                page_numbers.append(int(match.group(1)))
        except Exception:
            continue

    # Title, URL fall‑backs – one call each instead of multiple inside the loop above
    title_match = re.search(r"Page\\s+(\\d+)", page.title(), re.IGNORECASE)
    if title_match:
        page_numbers.append(int(title_match.group(1)))
    url_match = re.search(r"page-(\\d+)", page.url, re.IGNORECASE)
    if url_match:
        page_numbers.append(int(url_match.group(1)))

    return max(page_numbers) if page_numbers else 1


def extract_videos_from_page(page) -> list:
    """Collect video links with their associated images and meta data.
    The function now caches the ``.count()`` results to avoid re‑enumerating the DOM.
    """
    results = []
    posts = page.locator(".message")
    total_posts = posts.count()
    for i in range(total_posts):
        post = posts.nth(i)
        post_id = post.get_attribute("id") or f"post-{i+1}"

        # Username
        username_elem = post.locator(".message-name .username, .username").first
        username = username_elem.inner_text().strip() if username_elem.count() else "Unknown"

        # Post title
        title_elem = post.locator(".message-subject, .post-title, h1, h2").first
        post_title = title_elem.inner_text().strip() if title_elem.count() else ""

        # Content container – skip if missing
        content = post.locator(".bbWrapper")
        if not content.count():
            continue

        # Images – cache count
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
                matched_img = img_urls[video_idx] if video_idx < len(img_urls) else (img_urls[0] if img_urls else "")
                video_idx += 1
                results.append({
                    "post_id": post_id,
                    "username": username,
                    "post_title": post_title,
                    "image_url": matched_img,
                    "video_url": url,
                    "provider": urlparse(url).hostname or "",
                    "link_name": anchor.inner_text().strip(),
                    "source_page": page.url,
                })

    # Deduplicate by video_url (still O(n) but simple)
    unique = {item["video_url"]: item for item in results}
    return list(unique.values())


def is_cdp_ready(host="127.0.0.1", port=9222, timeout=0.8) -> bool:
    import socket
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def scrape_live_page(target_page_num: int | None = None, thread_key: str = "live_show") -> dict:
    """Scrape a single page of a forum thread.
    The function now performs a single ``goto`` when possible and avoids excessive waiting.
    """
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
        # Re‑use an existing page if it already points to the thread, otherwise open a new one.
        tab = next((t for t in context.pages if target_thread_id in t.url and "Log in" not in t.title()), None)
        if tab is None:
            tab = next((t for t in context.pages if ("/threads/" in t.url or "semprot.com" in t.url) and "Log in" not in t.title()), None)
        if tab is None:
            tab = context.pages[0] if context.pages else context.new_page()

        # Ensure we are on the correct thread page.
        if target_thread_id not in tab.url:
            page_to_open = target_page_num or default_page_num
            initial_target_url = f"{default_base_url}/page-{page_to_open}"
            tab.goto(initial_target_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(800)  # small pause for dynamic content

        base_url = get_base_thread_url(tab.url)
        latest_page = max(get_latest_page_number(tab), default_page_num)

        if target_page_num is None:
            m_curr = re.search(r"page-(\\d+)", tab.url)
            current_page_num = int(m_curr.group(1)) if m_curr else latest_page
        else:
            current_page_num = int(target_page_num)

        target_url = f"{base_url}/page-{current_page_num}"
        if tab.url.rstrip('/') != target_url.rstrip('/'):
            tab.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(800)

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
            "thread_name": thread_info["name"],
        }
