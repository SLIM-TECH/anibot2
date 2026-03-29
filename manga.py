import telebot
from telebot.types import Message, CallbackQuery

from shikimori import search_manga, get_manga_detail
from inline import count_kb, cancel_kb
from sender import send_manga_card
from states import set_state, get_state, clear_state, in_state


def register_manga_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["manga"])
    def cmd_manga(message: Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            _ask_count(bot, message, parts[1].strip())
        else:
            set_state(message.from_user.id, "manga:await_query")
            bot.send_message(
                message.chat.id,
                "📚 <b>Поиск манги</b>\n\nВведи название манги:",
                reply_markup=cancel_kb(),
            )

    @bot.message_handler(func=lambda m: m.text == "📚 Манга")
    def menu_manga(message: Message) -> None:
        set_state(message.from_user.id, "manga:await_query")
        bot.send_message(
            message.chat.id,
            "📚 <b>Поиск манги</b>\n\nВведи название:",
            reply_markup=cancel_kb(),
        )

    @bot.message_handler(func=lambda m: in_state(m.from_user.id, "manga:await_query"))
    def handle_manga_query(message: Message) -> None:
        query = (message.text or "").strip()
        clear_state(message.from_user.id)
        if not query:
            bot.send_message(message.chat.id, "Нужно ввести название манги.")
            return
        _ask_count(bot, message, query)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("count:") and in_state(c.from_user.id, "manga:await_count"))
    def handle_manga_count(call: CallbackQuery) -> None:
        state = get_state(call.from_user.id)
        clear_state(call.from_user.id)
        limit = int(call.data.split(":")[1])
        query = state.get("query", "") if state else ""
        bot.edit_message_text(f"⏳ Ищем мангу <b>{query}</b>...", call.message.chat.id, call.message.message_id)
        _do_manga_search(bot, call.message, query, limit, call.from_user)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("mpdf:"))
    def handle_manga_pdf(call: CallbackQuery) -> None:
        manga_id = int(call.data.split(":")[1])
        detail = get_manga_detail(manga_id)
        if not detail:
            bot.send_message(call.message.chat.id, "Не удалось загрузить информацию о манге.")
            return

        pdf_url = _find_pdf_url(detail)
        if pdf_url:
            try:
                bot.send_document(call.message.chat.id, pdf_url, caption="📄 Найден PDF манги")
                return
            except Exception:
                bot.send_message(call.message.chat.id, f"📄 PDF найден: <a href='{pdf_url}'>скачать</a>")
                return

        url = detail.get("url") or ""
        if not url.startswith("http"):
            url = f"https://shikimori.one{url}"

        bot.send_message(
            call.message.chat.id,
            "📄 Для этой манги прямой PDF не найден.\n"
            f"📖 Открыть страницу манги: <a href='{url}'>ссылка</a>",
            disable_web_page_preview=True,
        )


def _ask_count(bot: telebot.TeleBot, message: Message, query: str) -> None:
    set_state(message.from_user.id, "manga:await_count", query=query)
    bot.send_message(
        message.chat.id,
        f"📚 Ищем мангу: <b>{query}</b>\n\nСколько результатов показать?",
        reply_markup=count_kb(),
    )


def _do_manga_search(bot: telebot.TeleBot, message: Message, query: str, limit: int, user) -> None:
    results = search_manga(query, limit=limit)
    if not results:
        bot.send_message(message.chat.id, f"😔 По запросу <b>{query}</b> манга не найдена.")
        return

    bot.send_message(message.chat.id, f"✅ Найдено манги: <b>{len(results)}</b> по «{query}»")
    for index, manga in enumerate(results, 1):
        send_manga_card(
            bot,
            message.chat.id,
            manga,
            index=index,
            user_id=user.id,
            username=user.username,
            query=query,
        )


def _find_pdf_url(data) -> str | None:
    stack = [data]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for value in current.values():
                if isinstance(value, str) and value.lower().startswith("http") and ".pdf" in value.lower():
                    return value
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return None
