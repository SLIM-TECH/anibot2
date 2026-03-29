from datetime import datetime

import telebot
from telebot.types import Message, CallbackQuery

from shikimori import get_anime_by_season
from inline import season_kb, year_kb, count_kb
from sender import send_anime_card
from states import set_state, get_state, clear_state, in_state

CURRENT_YEAR = datetime.now().year

SEASON_RU = {
    "spring": "🌸 Весна",
    "summer": "☀️ Лето",
    "fall": "🍂 Осень",
    "winter": "❄️ Зима",
}


def register_season_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["season"])
    def cmd_season(message: Message) -> None:
        _show_season_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda m: m.text == "📅 По сезону")
    def menu_season(message: Message) -> None:
        _show_season_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("season:"))
    def handle_season(call: CallbackQuery) -> None:
        season = call.data.split(":")[1]
        label = SEASON_RU.get(season, season)
        set_state(call.from_user.id, "season:await_year", season=season, label=label)
        bot.edit_message_text(
            f"📅 {label} — выбери год:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=year_kb(CURRENT_YEAR),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("year:"))
    def handle_year(call: CallbackQuery) -> None:
        year = int(call.data.split(":")[1])
        state = get_state(call.from_user.id)
        if not state:
            return

        season = state.get("season", "spring")
        label = state.get("label", "")
        set_state(call.from_user.id, "season:await_count", season=season, year=year, label=label)
        bot.edit_message_text(
            f"📅 {label} {year} — сколько аниме показать?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=count_kb(),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("count:") and in_state(c.from_user.id, "season:await_count"))
    def handle_season_count(call: CallbackQuery) -> None:
        state = get_state(call.from_user.id)
        clear_state(call.from_user.id)
        limit = int(call.data.split(":")[1])

        season = state.get("season", "spring") if state else "spring"
        year = state.get("year", CURRENT_YEAR) if state else CURRENT_YEAR
        label = state.get("label", "") if state else ""

        bot.edit_message_text(
            f"⏳ Загружаем: {label} {year}...",
            call.message.chat.id,
            call.message.message_id,
        )

        results = get_anime_by_season(year, season, limit=limit)
        if not results:
            bot.send_message(call.message.chat.id, f"😔 Аниме для {label} {year} не найдены.")
            return

        bot.send_message(call.message.chat.id, f"📅 <b>{label} {year} — {len(results)} аниме</b>")
        for index, anime in enumerate(results, 1):
            send_anime_card(
                bot,
                call.message.chat.id,
                anime,
                index=index,
                user_id=call.from_user.id,
                username=call.from_user.username,
                command="season",
                query=f"{season}_{year}",
            )


def _show_season_menu(bot: telebot.TeleBot, chat_id: int) -> None:
    bot.send_message(
        chat_id,
        "📅 <b>Аниме по сезону</b>\n\nВыбери время года:",
        reply_markup=season_kb(),
    )
