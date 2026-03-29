import re
from typing import Any, Optional

import requests
from loguru import logger

from config import KODIK_BASE_URL, KODIK_TOKEN, ANILIBRIA_FALLBACK_BASE_URLS


_KODIK_WARNING_EMITTED = False
_ANILIBRIA_WARNING_EMITTED = False
_ANILIBRIA_STATUS_WARNED: set[str] = set()


def _session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _has_token() -> bool:
    return bool(KODIK_TOKEN) and KODIK_TOKEN != "YOUR_KODIK_TOKEN_HERE"


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http"):
        return url
    if url.startswith("//"):
        return "https:" + url
    return url


def _absolute_url(host: str, path_or_url: str) -> str:
    url = _normalize_url(path_or_url)
    if not url:
        return ""
    if url.startswith("http"):
        return url

    safe_host = (host or "").strip().rstrip("/")
    if not safe_host:
        return ""
    if not safe_host.startswith("http"):
        safe_host = "https://" + safe_host.lstrip("/")

    if url.startswith("/"):
        return safe_host + url
    return safe_host + "/" + url


def search_by_shikimori_id(shikimori_id: int) -> list[dict[str, Any]]:
    if not _has_token():
        return []

    try:
        response = _session().post(
            f"{KODIK_BASE_URL}/search",
            data={
                "token": KODIK_TOKEN,
                "shikimori_id": shikimori_id,
                "with_episodes": True,
                "with_material_data": True,
                "limit": 100,
            },
            timeout=15,
        )
        if response.status_code == 200:
            return response.json().get("results", [])
    except requests.RequestException as error:
        logger.error(f"Kodik error: {error}")

    return []


def _search_anilibria(query: str, limit: int = 8) -> list[dict]:
    if not query:
        return []

    for base_url in ANILIBRIA_FALLBACK_BASE_URLS:
        try:
            response = _session().get(
                f"{base_url.rstrip('/')}/title/search",
                params={"search": query, "limit": limit},
                timeout=15,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("list") or []
                return []

            warn_key = f"{base_url}:{response.status_code}"
            if warn_key not in _ANILIBRIA_STATUS_WARNED:
                logger.warning(f"AniLibria search status: {response.status_code} ({base_url})")
                _ANILIBRIA_STATUS_WARNED.add(warn_key)
        except requests.RequestException as error:
            logger.error(f"AniLibria search error ({base_url}): {error}")

    return []


def _parse_kodik_sources(results: list[dict]) -> list[dict]:
    sources: list[dict] = []

    for item in results:
        translation = item.get("translation") or {}
        seasons = item.get("seasons") or {}
        parsed_seasons: dict[int, dict[int, dict]] = {}
        episodes_count = 0

        for season_key, season_data in seasons.items():
            try:
                season_number = int(season_key)
            except (TypeError, ValueError):
                continue

            episodes = season_data.get("episodes") or {}
            parsed_episodes: dict[int, dict] = {}
            for ep_key, ep_data in episodes.items():
                try:
                    ep_number = int(ep_key)
                except (TypeError, ValueError):
                    continue
                if isinstance(ep_data, dict):
                    parsed_episodes[ep_number] = ep_data

            if parsed_episodes:
                parsed_seasons[season_number] = parsed_episodes
                episodes_count += len(parsed_episodes)

        if not parsed_seasons:
            continue

        title = translation.get("title") or "Неизвестный источник"
        link = _normalize_url(item.get("link") or "")
        sources.append(
            {
                "title": title,
                "type": translation.get("type") or "voice",
                "link": link,
                "episodes_count": episodes_count,
                "seasons": parsed_seasons,
            }
        )

    sources.sort(key=lambda src: (src["type"] != "voice", src["title"]))
    return sources


def _parse_anilibria_sources(items: list[dict]) -> list[dict]:
    sources: list[dict] = []

    for item in items:
        player = item.get("player") or {}
        raw_list = player.get("list") or {}
        host = (player.get("host") or "").strip()

        if not isinstance(raw_list, dict):
            continue

        episodes: dict[int, dict] = {}
        for ep_key, ep_data in raw_list.items():
            try:
                episode_number = int(str(ep_key).strip())
            except (TypeError, ValueError):
                continue

            if not isinstance(ep_data, dict):
                continue

            episode_urls: dict[str, str] = {}
            hls = ep_data.get("hls")
            if isinstance(hls, dict):
                for quality_key, quality_url in hls.items():
                    if isinstance(quality_url, str):
                        final_url = _absolute_url(host, quality_url)
                        if final_url:
                            episode_urls[str(quality_key)] = final_url
            elif isinstance(hls, str):
                final_url = _absolute_url(host, hls)
                if final_url:
                    episode_urls["hls"] = final_url

            if episode_urls:
                episodes[episode_number] = episode_urls

        if not episodes:
            continue

        names = item.get("names") or {}
        release_code = item.get("code") or ""
        release_title = names.get("ru") or names.get("en") or release_code or "AniLibria"
        release_link = f"https://www.anilibria.tv/release/{release_code}.html" if release_code else ""

        sources.append(
            {
                "title": f"AniLibria · {release_title}",
                "type": "voice",
                "link": release_link,
                "episodes_count": len(episodes),
                "seasons": {1: episodes},
            }
        )

    return sources


def _search_in_anilibria_by_titles(*titles: str) -> list[dict]:
    for title in titles:
        cleaned = (title or "").strip()
        if not cleaned:
            continue

        items = _search_anilibria(cleaned, limit=8)
        parsed = _parse_anilibria_sources(items)
        if parsed:
            return parsed

    return []


def _search_animego_anime_url(query: str) -> str:
    if not query:
        return ""
    try:
        response = _session().get(
            "https://animego.me/search/all",
            params={"q": query},
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if response.status_code != 200:
            return ""
        html = response.text or ""
        matches = re.findall(r'href="(/anime/(?!status|season|random)[^"]+-\d+)"', html)
        if not matches:
            return ""
        return "https://animego.me" + matches[0]
    except requests.RequestException as error:
        logger.error(f"AnimeGo search error: {error}")
        return ""


def _animego_episode_map(anime_url: str) -> dict[int, dict]:
    match = re.search(r"-(\d+)$", anime_url.rstrip("/"))
    if not match:
        return {}

    anime_id = match.group(1)

    try:
        response = _session().get(
            f"https://animego.me/player/{anime_id}",
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": anime_url,
            },
        )
        if response.status_code != 200:
            return {}

        content = ((response.json() or {}).get("data") or {}).get("content") or ""
        entries = re.findall(
            r'data-episode-number="(\d+)"[\s\S]*?data-episode="(\d+)"',
            content,
            flags=re.I,
        )

        result: dict[int, dict] = {}
        for number_str, episode_id_str in entries:
            try:
                number = int(number_str)
                episode_id = int(episode_id_str)
            except ValueError:
                continue
            result[number] = {
                "animego_episode_id": episode_id,
                "animego_referer": anime_url,
            }
        return result
    except requests.RequestException as error:
        logger.error(f"AnimeGo episode map error: {error}")
        return {}


def _search_in_animego_by_titles(*titles: str) -> list[dict]:
    for raw in titles:
        title = (raw or "").strip()
        if not title:
            continue

        anime_url = _search_animego_anime_url(title)
        if not anime_url:
            continue

        episodes = _animego_episode_map(anime_url)
        if not episodes:
            continue

        return [
            {
                "title": "AnimeGo",
                "type": "voice",
                "link": anime_url + "#player",
                "episodes_count": len(episodes),
                "seasons": {1: episodes},
            }
        ]
    return []


def get_episode_sources(shikimori_id: int, title_ru: str = "", title_en: str = "") -> list[dict]:
    global _KODIK_WARNING_EMITTED, _ANILIBRIA_WARNING_EMITTED

    kodik_sources = _parse_kodik_sources(search_by_shikimori_id(shikimori_id))
    if kodik_sources:
        return kodik_sources

    if not _has_token() and not _KODIK_WARNING_EMITTED:
        logger.warning("Kodik token не задан, используем бесплатные fallback провайдеры")
        _KODIK_WARNING_EMITTED = True

    anilibria_sources = _search_in_anilibria_by_titles(title_ru, title_en)
    if anilibria_sources:
        return anilibria_sources

    animego_sources = _search_in_animego_by_titles(title_ru, title_en)
    if animego_sources:
        return animego_sources

    if not _ANILIBRIA_WARNING_EMITTED:
        logger.warning("AniLibria/AnimeGo не вернули эпизоды. Подключаю API-видео fallback.")
        _ANILIBRIA_WARNING_EMITTED = True
    return []


def _quality_rank(key: str) -> int:
    normalized = (key or "").lower()
    named = {
        "ultra": 2160,
        "4k": 2160,
        "2k": 1440,
        "fhd": 1080,
        "fullhd": 1080,
        "hd": 720,
        "sd": 480,
        "ld": 360,
        "hls": 540,
    }
    if normalized in named:
        return named[normalized]

    digits = "".join(ch for ch in normalized if ch.isdigit())
    return int(digits) if digits else 0


def _extract_urls(data: Any, collector: list[tuple[int, str]]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            quality = _quality_rank(str(key))
            if isinstance(value, str):
                url = _normalize_url(value)
                if url.startswith("http"):
                    collector.append((quality, url))
            else:
                _extract_urls(value, collector)
    elif isinstance(data, list):
        for item in data:
            _extract_urls(item, collector)


def get_best_episode_media_url(episode_data: dict, fallback_link: Optional[str] = None) -> Optional[str]:
    if isinstance(episode_data, dict) and episode_data.get("animego_episode_id"):
        try:
            episode_id = int(episode_data["animego_episode_id"])
            referer = episode_data.get("animego_referer") or "https://animego.me/"
            response = _session().get(
                f"https://animego.me/player/videos/{episode_id}",
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": referer,
                },
            )
            if response.status_code == 200:
                content = ((response.json() or {}).get("data") or {}).get("content") or ""
                entries = re.findall(
                    r'data-player="([^"]+)"[^>]*data-provider-title="([^"]+)"',
                    content,
                    flags=re.I,
                )
                if entries:
                    entries.sort(key=lambda item: (item[1].lower() != "kodik", item[1]))
                    return _normalize_url(entries[0][0])
        except (ValueError, requests.RequestException) as error:
            logger.error(f"AnimeGo episode video error: {error}")

    candidates: list[tuple[int, str]] = []
    _extract_urls(episode_data, candidates)
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    fallback = _normalize_url(fallback_link or "")
    return fallback or None


def _jikan_search(query: str) -> list[dict]:
    try:
        response = _session().get(
            "https://api.jikan.moe/v4/anime",
            params={"q": query, "limit": 3, "sfw": True},
            timeout=20,
            headers={"User-Agent": "AniBot/2.0"},
        )
        if response.status_code == 200:
            payload = response.json() or {}
            return payload.get("data") or []
    except requests.RequestException as error:
        logger.error(f"Jikan search error: {error}")
    return []


def _jikan_videos(mal_id: int) -> list[dict]:
    try:
        response = _session().get(
            f"https://api.jikan.moe/v4/anime/{mal_id}/videos",
            timeout=20,
            headers={"User-Agent": "AniBot/2.0"},
        )
        if response.status_code == 200:
            payload = response.json() or {}
            data = payload.get("data") or {}
            videos: list[dict] = []
            for promo in data.get("promo") or []:
                trailer = promo.get("trailer") or {}
                url = trailer.get("url") or trailer.get("embed_url")
                if url:
                    videos.append({
                        "title": promo.get("title") or "Promo",
                        "url": _normalize_url(url),
                        "provider": "Jikan",
                    })
            for item in data.get("music_videos") or []:
                video = item.get("video") or {}
                url = video.get("url") or video.get("embed_url")
                if url:
                    videos.append({
                        "title": item.get("title") or "Music Video",
                        "url": _normalize_url(url),
                        "provider": "Jikan",
                    })
            return videos
    except requests.RequestException as error:
        logger.error(f"Jikan videos error: {error}")
    return []


def _anilist_trailer(query: str) -> list[dict]:
    graphql = """
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        title { romaji english native }
        trailer { site id }
      }
    }
    """

    try:
        response = _session().post(
            "https://graphql.anilist.co",
            json={"query": graphql, "variables": {"search": query}},
            timeout=20,
            headers={"User-Agent": "AniBot/2.0"},
        )
        if response.status_code != 200:
            return []

        media = ((response.json() or {}).get("data") or {}).get("Media") or {}
        trailer = media.get("trailer") or {}
        if trailer.get("site") != "youtube" or not trailer.get("id"):
            return []

        title_obj = media.get("title") or {}
        title = title_obj.get("english") or title_obj.get("romaji") or title_obj.get("native") or query
        return [
            {
                "title": f"{title} Trailer",
                "url": f"https://www.youtube.com/watch?v={trailer['id']}",
                "provider": "AniList",
            }
        ]
    except requests.RequestException as error:
        logger.error(f"AniList trailer error: {error}")
    return []


def get_free_video_links(*titles: str, limit: int = 8) -> list[dict]:
    links: list[dict] = []
    seen: set[str] = set()

    for raw_title in titles:
        title = (raw_title or "").strip()
        if not title:
            continue

        for anime in _jikan_search(title):
            mal_id = anime.get("mal_id")
            if not mal_id:
                continue
            for video in _jikan_videos(int(mal_id)):
                url = video.get("url") or ""
                if url and url not in seen:
                    seen.add(url)
                    links.append(video)
                    if len(links) >= limit:
                        return links

        for video in _anilist_trailer(title):
            url = video.get("url") or ""
            if url and url not in seen:
                seen.add(url)
                links.append(video)
                if len(links) >= limit:
                    return links

    return links
