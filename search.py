import telebot
from telebot.types import Message, CallbackQuery
from urllib.parse import quote_plus

from shikimori import search_anime, get_anime_detail, get_anime_videos, get_shikimori_url
from kodik import get_episode_sources, get_best_episode_media_url, get_free_video_links
from inline import count_kb, cancel_kb, source_kb, watch_season_kb
from sender import send_anime_card
from states import set_state, get_state, clear_state, in_state


WATCH_CONTEXT: dict[int, dict] = {}


def register_search_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["search"])
    def cmd_search(message: Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            _ask_count(bot, message, parts[1].strip(), source="search")
        else:
            set_state(message.from_user.id, "search:await_query")
            bot.send_message(
                message.chat.id,
                "🔎 <b>Поиск аниме</b>\n\nВведи название (русское, английское или японское):",
                reply_markup=cancel_kb(),
            )

    @bot.message_handler(func=lambda m: m.text == "🔎 Поиск аниме")
    def menu_search(message: Message) -> None:
        set_state(message.from_user.id, "search:await_query")
        bot.send_message(
            message.chat.id,
            "🔎 <b>Поиск аниме</b>\n\nВведи название:",
            reply_markup=cancel_kb(),
        )

    @bot.message_handler(func=lambda m: in_state(m.from_user.id, "search:await_query"))
    def handle_search_query(message: Message) -> None:
        query = (message.text or "").strip()
        clear_state(message.from_user.id)
        if not query:
            bot.send_message(message.chat.id, "Нужно ввести текст для поиска.")
            return
        _ask_count(bot, message, query, source="search")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("count:") and in_state(c.from_user.id, "search:await_count"))
    def handle_search_count(call: CallbackQuery) -> None:
        state = get_state(call.from_user.id)
        clear_state(call.from_user.id)
        limit = int(call.data.split(":")[1])
        query = state.get("query", "") if state else ""
        bot.edit_message_text(f"⏳ Ищем <b>{query}</b>...", call.message.chat.id, call.message.message_id)
        _do_search(bot, call.message, query, limit, user=call.from_user)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("watchsel:"))
    def handle_watch_select(call: CallbackQuery) -> None:
        anime_id = int(call.data.split(":")[1])
        bot.answer_callback_query(call.id, "Ищу источники...")

        detail = get_anime_detail(anime_id) or {}
        title_ru = detail.get("russian") or ""
        title_en = detail.get("name") or ""

        sources = get_episode_sources(anime_id, title_ru=title_ru, title_en=title_en)
        if not sources:
            free_links = get_free_video_links(title_ru, title_en, limit=8)

            shiki_links = [
                {
                    "title": item.get("name") or "Shikimori video",
                    "url": item.get("url"),
                    "provider": "Shikimori",
                }
                for item in get_anime_videos(anime_id)
                if isinstance(item, dict) and item.get("url")
            ]

            merged_links: list[dict] = []
            seen: set[str] = set()
            for entry in free_links + shiki_links:
                url = (entry.get("url") or "").strip()
                if url and url not in seen:
                    seen.add(url)
                    merged_links.append(entry)
                if len(merged_links) >= 8:
                    break

            if merged_links:
                lines = []
                for idx, item in enumerate(merged_links, 1):
                    provider = item.get("provider") or "Source"
                    title = item.get("title") or f"Видео {idx}"
                    url = item.get("url")
                    lines.append(f"• <a href='{url}'>{provider}: {title}</a>")
                bot.send_message(
                    call.message.chat.id,
                    "😔 Полных серий в открытых API сейчас нет.\n"
                    "Нашёл доступные бесплатные видео-ссылки:\n"
                    + "\n".join(lines),
                    disable_web_page_preview=True,
                )
                return

            bot.send_message(
                call.message.chat.id,
                "😔 Не нашёл эпизоды и даже fallback-видео.\n"
                "Для стабильной отправки серий нужен рабочий провайдер (например Kodik token).",
            )
            bot.send_message(
                call.message.chat.id,
                "🔎 Быстрые ссылки для поиска просмотра:\n"
                + "\n".join(_build_manual_links(title_ru, title_en, anime_id)),
                disable_web_page_preview=True,
            )
            return

        WATCH_CONTEXT[call.from_user.id] = {"anime_id": anime_id, "sources": sources}
        bot.send_message(
            call.message.chat.id,
            "🎧 Выбери источник / озвучку:",
            reply_markup=source_kb(sources),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("vsrc:"))
    def handle_watch_source(call: CallbackQuery) -> None:
        context = WATCH_CONTEXT.get(call.from_user.id)
        if not context:
            bot.answer_callback_query(call.id, "Контекст устарел, выбери аниме заново.")
            return

        source_idx = int(call.data.split(":")[1])
        sources = context.get("sources") or []
        if source_idx >= len(sources):
            bot.answer_callback_query(call.id, "Источник не найден.")
            return

        seasons = sorted((sources[source_idx].get("seasons") or {}).keys())
        if not seasons:
            bot.answer_callback_query(call.id, "Сезоны не найдены.")
            return

        bot.send_message(
            call.message.chat.id,
            "📺 Выбери сезон:",
            reply_markup=watch_season_kb(source_idx, seasons),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("vseason:"))
    def handle_watch_season(call: CallbackQuery) -> None:
        parts = call.data.split(":")
        if len(parts) != 3:
            return

        source_idx = int(parts[1])
        season = int(parts[2])

        context = WATCH_CONTEXT.get(call.from_user.id)
        if not context:
            bot.answer_callback_query(call.id, "Контекст устарел, выбери аниме заново.")
            return

        sources = context.get("sources") or []
        if source_idx >= len(sources):
            bot.answer_callback_query(call.id, "Источник не найден.")
            return

        episodes_map = (sources[source_idx].get("seasons") or {}).get(season) or {}
        if not episodes_map:
            bot.answer_callback_query(call.id, "Серии не найдены.")
            return

        available = sorted(episodes_map.keys())
        set_state(
            call.from_user.id,
            "watch:await_episode",
            source_idx=source_idx,
            season=season,
            available=available,
        )

        hint = f"{available[0]}-{available[-1]}" if available else ""
        bot.send_message(
            call.message.chat.id,
            f"✍️ Введи номер серии для сезона <b>{season}</b> (доступно: {hint}):",
            reply_markup=cancel_kb(),
        )

    @bot.message_handler(func=lambda m: in_state(m.from_user.id, "watch:await_episode"))
    def handle_watch_episode_input(message: Message) -> None:
        state = get_state(message.from_user.id)
        clear_state(message.from_user.id)
        context = WATCH_CONTEXT.get(message.from_user.id)

        if not state or not context:
            bot.send_message(message.chat.id, "Контекст устарел. Выбери аниме заново.")
            return

        try:
            episode_number = int((message.text or "").strip())
        except ValueError:
            bot.send_message(message.chat.id, "Номер серии должен быть числом.")
            return

        source_idx = state.get("source_idx")
        season = state.get("season")
        sources = context.get("sources") or []
        if source_idx is None or source_idx >= len(sources):
            bot.send_message(message.chat.id, "Источник не найден.")
            return

        source = sources[source_idx]
        episodes_map = (source.get("seasons") or {}).get(season) or {}
        episode_data = episodes_map.get(episode_number)

        if not episode_data:
            bot.send_message(message.chat.id, f"Серия {episode_number} не найдена в выбранном сезоне.")
            return

        media_url = get_best_episode_media_url(episode_data, source.get("link"))
        if not media_url:
            bot.send_message(message.chat.id, "Не удалось получить ссылку на видео.")
            return

        anime_id = context.get("anime_id")
        detail = get_anime_detail(anime_id) if anime_id else None
        title = (detail or {}).get("russian") or (detail or {}).get("name") or "Аниме"
        anime_url = get_shikimori_url(detail) if detail else "https://shikimori.one"

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"Сезон: <b>{season}</b> · Серия: <b>{episode_number}</b>\n"
            f"Качество: <b>лучшее доступное</b>"
        )

        try:
            bot.send_video(message.chat.id, media_url, caption=caption)
        except Exception:
            bot.send_message(
                message.chat.id,
                caption + f"\n\n🔗 <a href='{media_url}'>Открыть видео</a>\n🌐 <a href='{anime_url}'>Страница аниме</a>",
                disable_web_page_preview=True,
            )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("detail:"))
    def handle_detail(call: CallbackQuery) -> None:
        anime_id = int(call.data.split(":")[1])
        bot.answer_callback_query(call.id, "Загружаем детали...")
        detail = get_anime_detail(anime_id)
        if not detail:
            bot.send_message(call.message.chat.id, "😔 Не удалось загрузить подробности.")
            return

        studios = [studio.get("name") for studio in (detail.get("studios") or [])]
        videos = get_anime_videos(anime_id)
        trailers = [video for video in videos if video.get("kind") == "pv"]

        lines = [
            "📊 <b>Подробная информация</b>",
            "",
            f"🏢 <b>Студия:</b> {', '.join(filter(None, studios)) or '—'}",
            f"📅 <b>Дата выхода:</b> {(detail.get('aired_on') or '')[:10] or '—'}",
            f"🔤 <b>Японское название:</b> {detail.get('japanese') or '—'}",
            f"🧬 <b>Франшиза:</b> {detail.get('franchise') or '—'}",
            f"❤️ <b>В избранном:</b> {detail.get('favourites_count') or '—'}",
        ]

        if trailers:
            trailer_links = [f"<a href='{item['url']}'>{item.get('name') or 'Трейлер'}</a>" for item in trailers[:3] if item.get("url")]
            if trailer_links:
                lines.append(f"🎞 <b>Трейлеры:</b> {' · '.join(trailer_links)}")

        lines.append(f"🌐 <a href='{get_shikimori_url(detail)}'>Открыть страницу аниме</a>")
        bot.send_message(call.message.chat.id, "\n".join(lines), disable_web_page_preview=True)

    @bot.callback_query_handler(func=lambda c: c.data == "cancel")
    def handle_cancel(call: CallbackQuery) -> None:
        clear_state(call.from_user.id)
        bot.edit_message_text("❌ Действие отменено.", call.message.chat.id, call.message.message_id)


def _ask_count(bot: telebot.TeleBot, message: Message, query: str, source: str) -> None:
    set_state(message.from_user.id, f"{source}:await_count", query=query)
    bot.send_message(
        message.chat.id,
        f"🔎 Ищем: <b>{query}</b>\n\nСколько результатов показать?",
        reply_markup=count_kb(),
    )


def _do_search(bot: telebot.TeleBot, message: Message, query: str, limit: int, user=None) -> None:
    if user is None:
        user = message.chat

    results = search_anime(query, limit=limit)
    if not results:
        bot.send_message(
            message.chat.id,
            f"😔 По запросу <b>{query}</b> ничего не найдено.\nПопробуй другое название.",
        )
        return

    bot.send_message(message.chat.id, f"✅ Найдено: <b>{len(results)}</b> результатов по «{query}»")
    for index, anime in enumerate(results, 1):
        send_anime_card(
            bot,
            message.chat.id,
            anime,
            index=index,
            user_id=getattr(user, "id", message.chat.id),
            username=getattr(user, "username", None),
            command="search",
            query=query,
        )


def _build_manual_links(title_ru: str, title_en: str, anime_id: int) -> list[str]:
    title = (title_ru or title_en or "").strip() or str(anime_id)
    q = quote_plus(title)
    return [
        f"• <a href='https://www.youtube.com/results?search_query={q}+anime+episode'>YouTube</a>",
        f"• <a href='https://animego.org/search/all?q={q}'>AnimeGo</a>",
        f"• <a href='https://www.anilibria.tv/search?find={q}'>AniLibria</a>",
        f"• <a href='https://shikimori.one/animes?search={q}'>Shikimori</a>",
    ]
