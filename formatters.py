from typing import Any

from shikimori import get_shikimori_url, score_to_stars, get_shikimori_manga_url


KIND_EMOJI: dict[str, str] = {
    "tv": "📺",
    "movie": "🎬",
    "ova": "💿",
    "ona": "🌐",
    "special": "⭐",
    "music": "🎵",
    "tv_special": "📡",
    "pv": "🎞",
    "cm": "📣",
}

STATUS_RU: dict[str, str] = {
    "anons": "🔜 Анонс",
    "ongoing": "🟢 Онгоинг",
    "released": "✅ Вышло",
}

MANGA_KIND_RU: dict[str, str] = {
    "manga": "Манга",
    "manhwa": "Манхва",
    "manhua": "Маньхуа",
    "novel": "Новелла",
    "one_shot": "Ваншот",
    "doujin": "Додзинси",
}


def format_anime_card(anime: dict[str, Any], index: int = 0) -> str:
    name_ru = (anime.get("russian") or "").strip()
    name_en = (anime.get("name") or "").strip()

    kind = anime.get("kind") or "tv"
    kind_icon = KIND_EMOJI.get(kind, "🎌")
    kind_upper = kind.upper().replace("_", " ")

    score = anime.get("score") or "0"
    score_str = score_to_stars(score)

    status = anime.get("status") or ""
    status_str = STATUS_RU.get(status, status or "—")

    episodes = anime.get("episodes") or 0
    episodes_aired = anime.get("episodes_aired") or 0
    ep_str = str(episodes) if episodes else (f"{episodes_aired}+" if episodes_aired else "?")

    aired_on = (anime.get("aired_on") or "")[:4]
    year = aired_on or "—"

    genres_raw = anime.get("genres") or []
    genres = [g.get("russian") or g.get("name") for g in genres_raw[:5]]
    genres_str = " · ".join(filter(None, genres)) or "—"

    url = get_shikimori_url(anime)
    num = f"{index}. " if index else ""

    description = ""
    raw = (anime.get("description") or "").strip()
    if raw:
        description = raw[:320] + ("..." if len(raw) > 320 else "")

    lines = [
        f"{num}{kind_icon} <b>{name_ru or name_en}</b>",
    ]
    if name_ru and name_en and name_ru.lower() != name_en.lower():
        lines.append(f"<i>{name_en}</i>")

    lines += [
        "",
        f"⭐ <b>Рейтинг:</b> {score_str}",
        f"📅 <b>Год:</b> {year}   {kind_icon} {kind_upper}",
        f"📋 <b>Серий:</b> {ep_str}   {status_str}",
        f"🎭 <b>Жанры:</b> {genres_str}",
    ]

    if description:
        lines += ["", f"📖 {description}"]

    lines += ["", f"🔗 <a href='{url}'>Страница на Shikimori</a>"]
    return "\n".join(lines)


def format_manga_card(manga: dict[str, Any], index: int = 0) -> str:
    name_ru = (manga.get("russian") or "").strip()
    name_en = (manga.get("name") or "").strip()
    kind = manga.get("kind") or "manga"
    kind_ru = MANGA_KIND_RU.get(kind, kind)

    score = manga.get("score") or "0"
    score_str = score_to_stars(score)

    status = STATUS_RU.get(manga.get("status") or "", manga.get("status") or "—")
    chapters = manga.get("chapters") or "?"
    volumes = manga.get("volumes") or "?"
    year = (manga.get("aired_on") or "")[:4] or "—"

    genres_raw = manga.get("genres") or []
    genres = [g.get("russian") or g.get("name") for g in genres_raw[:5]]
    genres_str = " · ".join(filter(None, genres)) or "—"

    url = get_shikimori_manga_url(manga)
    num = f"{index}. " if index else ""

    lines = [f"{num}📚 <b>{name_ru or name_en}</b>"]
    if name_ru and name_en and name_ru.lower() != name_en.lower():
        lines.append(f"<i>{name_en}</i>")

    lines += [
        "",
        f"⭐ <b>Рейтинг:</b> {score_str}",
        f"🧾 <b>Тип:</b> {kind_ru}",
        f"📅 <b>Год:</b> {year}",
        f"📖 <b>Глав:</b> {chapters}   📚 <b>Томов:</b> {volumes}",
        f"📡 <b>Статус:</b> {status}",
        f"🎭 <b>Жанры:</b> {genres_str}",
        "",
        f"🔗 <a href='{url}'>Страница манги</a>",
    ]
    return "\n".join(lines)


def format_history_card(record: Any, index: int) -> str:
    date_str = record.created_at.strftime("%d.%m.%Y %H:%M")
    name = record.anime_title_ru or record.anime_title or "—"
    name_en = record.anime_title or ""
    score = record.anime_score
    score_str = score_to_stars(score) if score else "—"
    kind = KIND_EMOJI.get(record.anime_kind or "", "🎌")
    url = record.anime_url or "https://shikimori.one"

    cmd_map = {
        "search": "🔎 Поиск",
        "manga": "📚 Манга",
        "top": "🏆 Топ",
        "genre": "🎭 Жанр",
        "season": "📅 Сезон",
    }
    cmd_label = cmd_map.get(record.command, record.command)

    lines = [
        f"<b>{index}.</b> {date_str}  {cmd_label}",
        f"{kind} <a href='{url}'><b>{name}</b></a>",
    ]
    if name_en and name_en != name:
        lines.append(f"<i>{name_en}</i>")
    lines.append(f"⭐ {score_str}   🔎 <code>{record.query}</code>")
    return "\n".join(lines)
