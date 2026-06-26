"""
Pexels API client — searches and downloads free stock videos.

Prioritises portrait-orientation clips for the 9:16 vertical format.
Implements local caching so the same video isn't downloaded twice.
"""

import hashlib
import logging
import random
import time
from pathlib import Path

import requests

import config

logger = logging.getLogger(__name__)

_API_BASE = "https://api.pexels.com"
_CACHE_DIR = config.TEMP_DIR / "pexels_cache"


def _headers() -> dict:
    if not config.PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY is not set.")
    return {"Authorization": config.PEXELS_API_KEY}


def _cache_path(url: str) -> Path:
    """Deterministic local path for a given download URL."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(url.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"{h}.mp4"


def search_videos(
    query: str,
    orientation: str = "portrait",
    per_page: int = 15,
) -> list[dict]:
    """Search Pexels for videos matching *query*.

    Returns a list of video result dicts (raw API format).
    """
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": per_page,
    }
    logger.info("Pexels: searching videos for '%s' …", query)
    resp = requests.get(f"{_API_BASE}/videos/search", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    logger.info("  → found %d results", len(videos))
    return videos


def _pick_best_file(video: dict) -> str | None:
    """Choose the best video file URL from a Pexels result.

    Prefers HD quality in portrait orientation.
    """
    files = video.get("video_files", [])
    # Sort: prefer higher resolution, but cap at 1920 height
    candidates = []
    for f in files:
        w = f.get("width", 0)
        h = f.get("height", 0)
        quality = f.get("quality", "")
        if h >= 720:
            candidates.append(f)

    if not candidates:
        candidates = files  # fallback to any available file

    if not candidates:
        return None

    # Prefer portrait orientation (height > width)
    portrait = [f for f in candidates if f.get("height", 0) > f.get("width", 0)]
    pool = portrait if portrait else candidates

    # Pick highest resolution that isn't absurdly large
    pool.sort(key=lambda f: f.get("height", 0), reverse=True)
    return pool[0].get("link")


def download_video(url: str, dest: Path | None = None) -> Path:
    """Download a video from *url*, returning the local path.

    Uses a content-addressable cache to avoid re-downloading.
    """
    cached = _cache_path(url)
    if dest is None:
        dest = cached

    if cached.exists():
        logger.info("Pexels: cache hit for %s", cached.name)
        if dest != cached:
            import shutil
            shutil.copy2(cached, dest)
        return dest

    logger.info("Pexels: downloading %s …", url[:80])
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            f.write(chunk)

    # Also save to cache
    if dest != cached:
        import shutil
        shutil.copy2(dest, cached)

    logger.info("  → saved to %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
    return dest


def fetch_video_for_keyword(keyword: str, dest: Path) -> Path | None:
    """High-level helper: search → pick best → download.

    Falls back to generic keywords if *keyword* yields no results.
    """
    for attempt_keyword in [keyword] + config.PEXELS_FALLBACK_KEYWORDS:
        videos = search_videos(attempt_keyword)
        if not videos:
            logger.warning("No results for '%s', trying fallback …", attempt_keyword)
            time.sleep(0.5)
            continue

        # Shuffle to add variety even when the same keyword recurs
        random.shuffle(videos)

        for video in videos:
            url = _pick_best_file(video)
            if url:
                return download_video(url, dest)

    logger.error("Could not find any video for keyword '%s' after all fallbacks.", keyword)
    return None


def fetch_videos_for_scenes(scenes: list[dict], temp_dir: Path) -> list[dict]:
    """Download a background video for every scene.

    Enriches each scene dict with ``video_path``.
    """
    enriched: list[dict] = []

    for idx, scene in enumerate(scenes):
        keyword = scene.get("search_keyword", "nature")
        dest = temp_dir / f"bg_{idx:03d}.mp4"

        path = fetch_video_for_keyword(keyword, dest)
        enriched.append({**scene, "video_path": str(path) if path else None})

        # Be polite to the API
        time.sleep(0.3)

    return enriched
