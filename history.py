import telebot
from telebot.types import Message, CallbackQuery

from service import get_history, clear_history
from inline import history_kb, confirm_clear_kb
from formatters import format_history_card


def register_history_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["history"])
    def cmd_history(message: Message) -> None:
        _show_history(bot, message.chat.id, message.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "📜 История")
    def menu_history(message: Message) -> None:
        _show_history(bot, message.chat.id, message.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "hist:clear")
    def hist_clear(call: CallbackQuery) -> None:
        bot.edit_message_text(
            "🗑 <b>Очистить всю историю?</b>\n\nЭто действие нельзя отменить.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=confirm_clear_kb(),
        )

    @bot.callback_query_handler(func=lambda c: c.data == "hist:confirm_clear")
    def hist_confirm_clear(call: CallbackQuery) -> None:
        count = clear_history(call.from_user.id)
        bot.edit_message_text(
            f"✅ Готово! Удалено записей: <b>{count}</b>",
            call.message.chat.id,
            call.message.message_id,
        )

    @bot.callback_query_handler(func=lambda c: c.data in ("hist:cancel_clear", "hist:close"))
    def hist_cancel(call: CallbackQuery) -> None:
        bot.edit_message_text("↩️ Закрыто.", call.message.chat.id, call.message.message_id)


def _show_history(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    records = get_history(user_id, limit=15)
    if not records:
        bot.send_message(
            chat_id,
            "📜 <b>История пуста</b>\n\nСделай поиск, и тут появятся запросы.",
        )
        return

    header = f"📜 <b>История поиска</b> (последние {len(records)}):\n\n"
    cards = "\n\n".join(format_history_card(record, index) for index, record in enumerate(records, 1))
    text = header + cards

    if len(text) > 4000:
        text = text[:3990] + "\n<i>...обрезано</i>"

    bot.send_message(
        chat_id,
        text,
        reply_markup=history_kb(),
        disable_web_page_preview=True,
    )
