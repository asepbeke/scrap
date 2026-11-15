import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

VIDEO_HOSTS = {
    "dood.to",
    "vidara.to",
    "vidara.so",
}

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
        "default_page": 1624,
        "db_file": "videos_req_live.db",
        "csv_file": "videos_req_live.csv",
        "icon": "fa-comments",
        "badge_color": "bg-amber-600"
    }
}


def is_video_link(url):
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


def get_base_thread_url(url):
    parsed = urlparse(url)
    clean_path = parsed.path.rstrip('/')
    base_path = re.sub(r'/page-\d+$', '', clean_path)
    return f"{parsed.scheme}://{parsed.netloc}{base_path}"


def get_latest_page_number(page):
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
            match = re.search(r'page-(\d+)', href)
            if match:
                page_numbers.append(int(match.group(1)))
        except Exception:
            continue

    title_match = re.search(r'Page\s+(\d+)', page.title(), re.IGNORECASE)
    if title_match:
        page_numbers.append(int(title_match.group(1)))

    url_match = re.search(r'page-(\d+)', page.url, re.IGNORECASE)
    if url_match:
        page_numbers.append(int(url_match.group(1)))

    return max(page_numbers) if page_numbers else 1


def extract_videos_from_page(page):
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

        # Content images
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


def is_cdp_ready(host="127.0.0.1", port=9222, timeout=0.8):
    import socket
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def scrape_live_page(target_page_num=None, thread_key="live_show"):
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

        # 1. Cari tab yang URL-nya secara spesifik sesuai thread_id
        tab = next(
            (t for t in context.pages if target_thread_id in t.url and "Log in" not in t.title()),
            None
        )

        # 2. Jika belum ada tab spesifik thread ini, cari sembarang tab forum yang aktif
        if tab is None:
            tab = next(
                (t for t in context.pages if ("/threads/" in t.url or "semprot.com" in t.url) and "Log in" not in t.title()),
                None
            )

        # 3. Jika tidak ada tab forum sama sekali, gunakan tab pertama atau buka tab baru
        if tab is None:
            if context.pages:
                tab = context.pages[0]
            else:
                tab = context.new_page()

        # Pastikan tab berada pada thread yang ditargetkan
        if target_thread_id not in tab.url:
            p_to_open = target_page_num or default_page_num
            initial_target_url = f"{default_base_url}/page-{p_to_open}"
            tab.goto(initial_target_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(800)

        base_url = get_base_thread_url(tab.url)
        latest_page = max(get_latest_page_number(tab), default_page_num)

        if target_page_num is None:
            # Gunakan nomor halaman dari URL tab saat ini, atau latest_page
            m_curr = re.search(r'page-(\d+)', tab.url)
            current_page_num = int(m_curr.group(1)) if m_curr else latest_page
        else:
            current_page_num = int(target_page_num)

        target_url = f"{base_url}/page-{current_page_num}"

        # Navigasikan jika tab belum di URL target
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
            "thread_name": thread_info["name"]
        }
