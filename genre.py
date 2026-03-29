import telebot
from telebot.types import Message, CallbackQuery

from shikimori import get_genres, get_anime_by_genre
from inline import genres_kb, count_kb
from sender import send_anime_card
from states import set_state, get_state, clear_state, in_state


def register_genre_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["genre"])
    def cmd_genre(message: Message) -> None:
        _show_genres(bot, message.chat.id)

    @bot.message_handler(func=lambda m: m.text == "🎭 По жанру")
    def menu_genre(message: Message) -> None:
        _show_genres(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("genre:"))
    def handle_genre(call: CallbackQuery) -> None:
        parts = call.data.split(":", 2)
        gid = int(parts[1])
        gname = parts[2] if len(parts) > 2 else "Жанр"
        set_state(call.from_user.id, "genre:await_count", genre_id=gid, genre_name=gname)
        bot.edit_message_text(
            f"🎭 Жанр: <b>{gname}</b>\n\nСколько аниме показать?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=count_kb(),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("count:") and in_state(c.from_user.id, "genre:await_count"))
    def handle_genre_count(call: CallbackQuery) -> None:
        state = get_state(call.from_user.id)
        clear_state(call.from_user.id)
        limit = int(call.data.split(":")[1])
        gid = state.get("genre_id") if state else None
        gname = state.get("genre_name", "") if state else ""

        bot.edit_message_text(
            f"⏳ Загружаем топ {limit} в жанре <b>{gname}</b>...",
            call.message.chat.id,
            call.message.message_id,
        )

        results = get_anime_by_genre(gid, limit=limit)
        if not results:
            bot.send_message(call.message.chat.id, "😔 Аниме в этом жанре не найдены.")
            return

        bot.send_message(call.message.chat.id, f"🎭 <b>Топ {len(results)} — {gname}</b>")
        for index, anime in enumerate(results, 1):
            send_anime_card(
                bot,
                call.message.chat.id,
                anime,
                index=index,
                user_id=call.from_user.id,
                username=call.from_user.username,
                command="genre",
                query=f"genre:{gname}",
            )


def _show_genres(bot: telebot.TeleBot, chat_id: int) -> None:
    wait = bot.send_message(chat_id, "⏳ Загружаем список жанров...")

    all_genres = get_genres()
    genres = [genre for genre in all_genres if genre.get("kind") == "genre"]
    bot.delete_message(chat_id, wait.message_id)
    if not genres:
        bot.send_message(chat_id, "😔 Не удалось загрузить жанры.")
        return

    bot.send_message(
        chat_id,
        f"🎭 <b>Выбери жанр</b> ({len(genres[:24])} жанров):",
        reply_markup=genres_kb(genres),
    )
