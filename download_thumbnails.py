"""Backward compatibility wrapper for download_thumbnails.py.

Delegates thumbnail downloading to app/services/thumbnail_service.py.
Maintains full compatibility with download_thumbs.bat.
"""

from app.services.thumbnail_service import ThumbnailService
from config import BASE_DIR

if __name__ == "__main__":
    def progress_reporter(completed: int, total: int, success: int, already: int, failed: int):
        print(f"[{completed}/{total}] Berhasil: {success} | Ada: {already} | Gagal: {failed}")

    print("==================================================")
    print("   Download Thumbnail Video")
    print(f"   Folder: {BASE_DIR / 'static' / 'thumbnails'}")
    print("==================================================")

    res = ThumbnailService.download_all(
        thread_key="live_show",
        base_dir=BASE_DIR,
        max_workers=12,
        progress_cb=progress_reporter,
    )

    print("\n========== SELESAI ==========")
    print(f"Total Video: {res['total']}")
    print(f"Berhasil Download Baru: {res['success']}")
    print(f"Sudah Ada Sebelumnya: {res['already']}")
    print(f"Gagal / Timeout: {res['failed']}")
    print(f"Lokasi file: {res['target_dir']}")
