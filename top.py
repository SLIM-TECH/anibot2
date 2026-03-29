import telebot
from telebot.types import Message, CallbackQuery

from shikimori import get_top_anime
from inline import top_kind_kb, count_kb
from sender import send_anime_card
from states import set_state, get_state, clear_state, in_state

KIND_LABELS = {
    "tv": "📺 Сериалы",
    "movie": "🎬 Фильмы",
    "ova": "💿 OVA",
    "ona": "🌐 ONA",
    "special": "⭐ Спешлы",
    "music": "🎵 Музыка",
}


def register_top_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["top"])
    def cmd_top(message: Message) -> None:
        _show_top_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda m: m.text == "🏆 Топ аниме")
    def menu_top(message: Message) -> None:
        _show_top_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("topkind:"))
    def handle_top_kind(call: CallbackQuery) -> None:
        kind = call.data.split(":")[1]
        label = KIND_LABELS.get(kind, kind)
        set_state(call.from_user.id, "top:await_count", kind=kind, label=label)
        bot.edit_message_text(
            f"🏆 Топ: <b>{label}</b>\n\nСколько показать?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=count_kb(),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("count:") and in_state(c.from_user.id, "top:await_count"))
    def handle_top_count(call: CallbackQuery) -> None:
        state = get_state(call.from_user.id)
        clear_state(call.from_user.id)
        limit = int(call.data.split(":")[1])
        kind = state.get("kind", "tv") if state else "tv"
        label = state.get("label", "") if state else ""

        bot.edit_message_text(
            f"⏳ Загружаем топ {limit} — {label}...",
            call.message.chat.id,
            call.message.message_id,
        )

        results = get_top_anime(limit=limit, kind=kind)
        if not results:
            bot.send_message(call.message.chat.id, "😔 Не удалось загрузить топ. Попробуй позже.")
            return

        bot.send_message(call.message.chat.id, f"🏆 <b>Топ {len(results)} — {label}</b>")
        for index, anime in enumerate(results, 1):
            send_anime_card(
                bot,
                call.message.chat.id,
                anime,
                index=index,
                user_id=call.from_user.id,
                username=call.from_user.username,
                command="top",
                query=f"top:{kind}",
            )


def _show_top_menu(bot: telebot.TeleBot, chat_id: int) -> None:
    bot.send_message(
        chat_id,
        "🏆 <b>Топ аниме по рейтингу Shikimori</b>\n\nВыбери тип:",
        reply_markup=top_kind_kb(),
    )
