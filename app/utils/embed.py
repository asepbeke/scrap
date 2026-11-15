"""Video embedding and streaming URL formatters."""

import re
from urllib.parse import urlparse


def format_embed_url(video_url: str, provider: str = "") -> str:
    """Format standard video link to an iframe-compatible embed URL.

    Handles:
    - DoodStream / Dood clones: /d/<id> -> /e/<id>
    - Playmogo: /d/<id> -> /e/<id>
    - Vidara: /v/<id> -> /e/<id>
    """
    if not video_url:
        return ""

    video_url = video_url.strip()
    provider = (provider or "").lower()

    # Dood & Playmogo embedding (/d/ -> /e/)
    if any(k in provider or k in video_url.lower() for k in ["dood", "playmogo"]):
        if "/d/" in video_url:
            return re.sub(r"/d/", "/e/", video_url)
        return video_url

    # Vidara embedding (/v/<id> -> /e/<id>)
    if "vidara" in provider or "vidara" in video_url.lower():
        m = re.search(r"/(?:v|e)/([a-zA-Z0-9]+)", video_url)
        if m:
            v_id = m.group(1)
            parsed = urlparse(video_url)
            host = parsed.netloc or "vidara.to"
            scheme = parsed.scheme or "https"
            return f"{scheme}://{host}/e/{v_id}"
        return re.sub(r"/v/", "/e/", video_url)

    return video_url
