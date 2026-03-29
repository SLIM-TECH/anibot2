import time
from typing import Any, Optional

import requests
from loguru import logger

from config import SHIKIMORI_BASE_URL, SHIKIMORI_HEADERS

_LAST_REQUEST: float = 0.0
_MIN_INTERVAL: float = 0.6


def _get(endpoint: str, params: Optional[dict] = None) -> Any:
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    url = f"{SHIKIMORI_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, headers=SHIKIMORI_HEADERS, params=params, timeout=15)
        _LAST_REQUEST = time.time()
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            logger.warning("Shikimori rate limit, пауза 3 сек...")
            time.sleep(3)
            return _get(endpoint, params)
        logger.error(f"Shikimori {resp.status_code}: {url}")
        return None
    except requests.RequestException as error:
        logger.error(f"Shikimori request error: {error}")
        return None


def search_anime(query: str, limit: int = 5) -> list[dict]:
    return _get("animes", {"search": query, "limit": limit, "order": "ranked"}) or []


def search_manga(query: str, limit: int = 5) -> list[dict]:
    return _get("mangas", {"search": query, "limit": limit, "order": "ranked"}) or []


def get_top_anime(limit: int = 5, kind: str = "tv") -> list[dict]:
    return _get("animes", {
        "order": "ranked",
        "kind": kind,
        "limit": limit,
        "status": "released",
    }) or []


def get_anime_by_genre(genre_id: int, limit: int = 5) -> list[dict]:
    return _get("animes", {
        "genre": genre_id,
        "order": "ranked",
        "limit": limit,
        "status": "released",
    }) or []


def get_anime_by_season(year: int, season: str, limit: int = 5) -> list[dict]:
    season_str = f"{season}_{year}"
    return _get("animes", {"season": season_str, "order": "ranked", "limit": limit}) or []


def get_anime_detail(anime_id: int) -> Optional[dict]:
    return _get(f"animes/{anime_id}")


def get_manga_detail(manga_id: int) -> Optional[dict]:
    return _get(f"mangas/{manga_id}")


def get_anime_videos(anime_id: int) -> list[dict]:
    return _get(f"animes/{anime_id}/videos") or []


def get_genres() -> list[dict]:
    return _get("genres") or []


def get_image_url(item: dict, size: str = "original") -> Optional[str]:
    image = item.get("image") or {}
    path = image.get(size) or image.get("original") or image.get("preview")
    if not path:
        return None
    if path.startswith("http"):
        return path
    return f"https://shikimori.one{path}"


def get_shikimori_url(anime: dict) -> str:
    url = anime.get("url") or ""
    if url.startswith("http"):
        return url
    return f"https://shikimori.one{url}"


def get_shikimori_manga_url(manga: dict) -> str:
    url = manga.get("url") or ""
    if url.startswith("http"):
        return url
    return f"https://shikimori.one{url}"


def score_to_stars(score: str | float | None) -> str:
    try:
        value = float(score or 0)
    except (ValueError, TypeError):
        return "—"
    filled = round(value / 2)
    return "★" * filled + "☆" * (5 - filled) + f"  {value:.2f}"
