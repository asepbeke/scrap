import csv
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# ==============================================================================
# KONFIGURASI SCRAPER THREAD: REQUEST & ASK LIVE SHOW
# Link: https://www.semprot.com/threads/request-ask-video-live-show-disini-dilarang-share-tanpa-ada-yang-request.1502696/page-1624
# ==============================================================================
THREAD_ID = "1502696"
BASE_THREAD_URL = "https://www.semprot.com/threads/request-ask-video-live-show-disini-dilarang-share-tanpa-ada-yang-request.1502696"
DEFAULT_TARGET_PAGE = 1624

DB_NAME = "videos_req_live.db"
CSV_NAME = "videos_req_live.csv"

# ==============================================================================
# PENGATURAN TARGET HALAMAN
# ==============================================================================
# Opsi 1: Isi CUSTOM_PAGE untuk scrape 1 halaman saja (misal: CUSTOM_PAGE = 1624)
# Opsi 2: Jalankan via terminal: 'python app_req_live.py 1624' atau 'python app_req_live.py 1620 1624'
# Opsi 3: Jika None, akan mengambil NUM_PAGES terakhir dari halaman terbaru
# ==============================================================================
CUSTOM_PAGE = 1624    # Default ke page 1624 sesuai permintaan, atau ubah sesuai kebutuhan
START_PAGE = None     # Contoh: 1620
END_PAGE = None       # Contoh: 1624
NUM_PAGES = 10        # Default jika CUSTOM_PAGE = None

VIDEO_HOSTS = {
    "dood.to",
    "vidara.to",
    "vidara.so",
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


def extract_videos(page):
    results = []

    posts = page.locator(".message")
    total_posts = posts.count()
    print(f"Total post di halaman ini: {total_posts}")

    for i in range(total_posts):
        post = posts.nth(i)
        post_id = post.get_attribute("id") or f"post-{i+1}"

        # Username
        username_element = post.locator(".message-name .username, .username").first
        username = (
            username_element.inner_text().strip()
            if username_element.count()
            else "Unknown"
        )

        # Post title (jika ada)
        title_element = post.locator(".message-subject, .post-title, h1, h2").first
        post_title = title_element.inner_text().strip() if title_element.count() else ""

        # Gambar / Thumbnail di dalam konten bbWrapper
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

        # Cari anchor video
        anchors = content.locator("a[href]")
        video_idx = 0
        for j in range(anchors.count()):
            anchor = anchors.nth(j)
            url = anchor.get_attribute("href")
            if not url or not url.startswith("http"):
                continue

            if is_video_link(url):
                # Pasangkan thumbnail gambar terdekat
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

    # Deduplikasi link video di dalam satu halaman
    unique = {}
    for item in results:
        unique[item["video_url"]] = item
    return list(unique.values())


def get_latest_page_number(page):
    page_numbers = []

    # 1. Navigasi elemen
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

    # 2. Judul tab
    title_match = re.search(r'Page\s+(\d+)', page.title(), re.IGNORECASE)
    if title_match:
        page_numbers.append(int(title_match.group(1)))

    # 3. URL tab
    url_match = re.search(r'page-(\d+)', page.url, re.IGNORECASE)
    if url_match:
        page_numbers.append(int(url_match.group(1)))

    return max(page_numbers) if page_numbers else DEFAULT_TARGET_PAGE


def save_database(results):
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            username TEXT,
            post_title TEXT,
            image_url TEXT,
            video_url TEXT UNIQUE,
            provider TEXT,
            link_name TEXT,
            source_page TEXT,
            created_at TEXT
        )
    """)

    now = datetime.now(timezone.utc).isoformat()
    new_records = 0

    for item in results:
        cur = conn.execute("""
            INSERT OR IGNORE INTO videos
            (post_id, username, post_title, image_url, video_url, provider, link_name,
             source_page, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["post_id"],
            item["username"],
            item["post_title"],
            item["image_url"],
            item["video_url"],
            item["provider"],
            item["link_name"],
            item.get("source_page", ""),
            now
        ))
        if cur.rowcount > 0:
            new_records += 1

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    conn.close()

    return total, new_records


def save_csv(results):
    with open(CSV_NAME, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "post_id",
                "username",
                "post_title",
                "image_url",
                "provider",
                "video_url",
                "link_name",
                "source_page"
            ],
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(results)


def main():
    print("=" * 60)
    print("SCRAPER THREAD: Request & Ask Live Show")
    print(f"Target Base URL: {BASE_THREAD_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
        except Exception as e:
            print("[ERROR] Tidak dapat terhubung ke Chrome pada port 9222.")
            print("Pastikan Google Chrome telah dibuka dengan: run_chrome.bat atau start_chrome.bat")
            print(f"Detail: {e}")
            return

        context = browser.contexts[0]

        # 1. Cari tab yang URL-nya memuat thread_id 1502696
        tab = next(
            (t for t in context.pages if THREAD_ID in t.url and "Log in" not in t.title()),
            None
        )

        # 2. Jika belum ada, gunakan tab forum apa pun yang terbuka
        if tab is None:
            tab = next(
                (t for t in context.pages if ("/threads/" in t.url or "semprot.com" in t.url) and "Log in" not in t.title()),
                None
            )

        # 3. Jika belum ada sama sekali, gunakan tab pertama atau buka baru
        if tab is None:
            tab = context.pages[0] if context.pages else context.new_page()

        # Evaluasi CLI arguments atau config
        cli_custom_start = None
        cli_custom_end = None
        if len(sys.argv) == 2:
            try:
                cli_custom_start = int(sys.argv[1])
                cli_custom_end = cli_custom_start
            except ValueError:
                pass
        elif len(sys.argv) >= 3:
            try:
                cli_custom_start = int(sys.argv[1])
                cli_custom_end = int(sys.argv[2])
            except ValueError:
                pass

        # Navigasi awal jika tab belum di thread target
        if THREAD_ID not in tab.url:
            init_page = cli_custom_start or CUSTOM_PAGE or DEFAULT_TARGET_PAGE
            init_url = f"{BASE_THREAD_URL}/page-{init_page}"
            print(f"[*] Mengarahkan tab browser ke thread: {init_url} ...")
            tab.goto(init_url, wait_until="domcontentloaded", timeout=30000)
            try:
                tab.wait_for_selector(".message", timeout=10000)
            except Exception:
                pass
            tab.wait_for_timeout(1000)

        print("[OK] Tab Aktif:", tab.title())
        print("[OK] URL Aktif:", tab.url)

        latest_page = max(get_latest_page_number(tab), DEFAULT_TARGET_PAGE)

        if cli_custom_start is not None:
            start_page = max(1, cli_custom_start)
            end_page = max(start_page, cli_custom_end if cli_custom_end is not None else start_page)
            print(f"[*] Mode CLI: Target Page {start_page} s/d {end_page}")
        elif CUSTOM_PAGE is not None:
            start_page = max(1, int(CUSTOM_PAGE))
            end_page = start_page
            print(f"[*] Mode Custom Page: Halaman {start_page}")
        elif START_PAGE is not None or END_PAGE is not None:
            start_page = max(1, int(START_PAGE or 1))
            end_page = int(END_PAGE or latest_page)
            print(f"[*] Mode Range: Halaman {start_page} s/d {end_page}")
        else:
            start_page = max(1, latest_page - NUM_PAGES + 1)
            end_page = latest_page
            print(f"[*] Mode Default: {NUM_PAGES} halaman terakhir ({start_page} s/d {end_page})")

        print(f"\nDetected latest page: {latest_page}")
        print(f"Target pages to scrape: {start_page} to {end_page} ({end_page - start_page + 1} pages)\n")

        all_results = []

        for p_num in range(start_page, end_page + 1):
            target_url = f"{BASE_THREAD_URL}/page-{p_num}"
            print(f"[{p_num}/{end_page}] Membuka: {target_url} ...")

            if tab.url.rstrip('/') != target_url.rstrip('/'):
                try:
                    tab.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    tab.wait_for_selector(".message", timeout=10000)
                except Exception as e:
                    print(f"Warning saat memuat halaman {p_num}: {e}")
                tab.wait_for_timeout(1000)

            page_videos = extract_videos(tab)
            print(f"-> Halaman {p_num} menemukan {len(page_videos)} link video.")
            all_results.extend(page_videos)

        # Deduplikasi
        unique_results = {}
        for item in all_results:
            if item["video_url"] not in unique_results:
                unique_results[item["video_url"]] = item
        final_results = list(unique_results.values())

        print(f"\nTotal video unik didapatkan: {len(final_results)}")

        total_db, new_db = save_database(final_results)
        save_csv(final_results)

        print("\n" + "=" * 30 + " SELESAI " + "=" * 30)
        print("Total video terextract:", len(final_results))
        print("Data baru masuk ke SQLite:", new_db)
        print("Total video di SQLite:", total_db)
        print("Tersimpan di CSV:", CSV_NAME)
        print("Tersimpan di SQLite:", DB_NAME)
        print("=" * 69)


if __name__ == "__main__":
    main()

