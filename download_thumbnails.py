import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import requests

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos.db")
THUMB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "thumbnails")

os.makedirs(THUMB_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
}


def download_single_thumbnail(item):
    video_id, image_url = item

    if not image_url or not image_url.startswith("http"):
        return False, video_id, "Invalid URL"

    target_path = os.path.join(THUMB_DIR, f"{video_id}.jpg")

    # Skip if already downloaded and has content
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
        return True, video_id, "Already exists"

    try:
        # Some hosts need referer matching their domain
        parsed = urlparse(image_url)
        custom_headers = dict(HEADERS)
        custom_headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

        response = requests.get(image_url, headers=custom_headers, timeout=12)
        if response.status_code == 200 and len(response.content) > 500:
            with open(target_path, "wb") as f:
                f.write(response.content)
            return True, video_id, "Success"
        else:
            return False, video_id, f"HTTP {response.status_code}"
    except Exception as e:
        return False, video_id, str(e)


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, image_url FROM videos WHERE image_url IS NOT NULL AND image_url != ''").fetchall()
    conn.close()

    total = len(rows)
    print("==================================================")
    print(f"   Download Thumbnail Video ({total} items)")
    print(f"   Folder: {THUMB_DIR}")
    print("==================================================")

    success_count = 0
    fail_count = 0
    already_count = 0

    max_workers = 12
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {executor.submit(download_single_thumbnail, row): row[0] for row in rows}

        completed = 0
        for future in as_completed(future_to_id):
            completed += 1
            ok, v_id, msg = future.result()
            if ok:
                if msg == "Already exists":
                    already_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1

            if completed % 50 == 0 or completed == total:
                print(f"[{completed}/{total}] Berhasil: {success_count} | Ada: {already_count} | Gagal: {fail_count}")

    print("\n========== SELESAI ==========")
    print(f"Total Video: {total}")
    print(f"Berhasil Download Baru: {success_count}")
    print(f"Sudah Ada Sebelumnya: {already_count}")
    print(f"Gagal / Timeout: {fail_count}")
    print(f"Lokasi file: {THUMB_DIR}")


if __name__ == "__main__":
    main()

