import telebot
from telebot.types import Message

from states import get_state


def register_unknown_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(func=lambda m: True)
    def handle_unknown(message: Message) -> None:
        text = message.text or ""
        uid = message.from_user.id

        state = get_state(uid)
        if state:
            bot.send_message(
                message.chat.id,
                "⚠️ Сейчас идёт диалог. Нажми <b>❌ Отмена</b> или заверши текущее действие.",
            )
            return

        if text.startswith("/"):
            bot.send_message(
                message.chat.id,
                f"❓ Неизвестная команда: <code>{text}</code>\n\nИспользуй /help для списка команд.",
            )
        else:
            bot.send_message(
                message.chat.id,
                "🤔 Не понял тебя. Используй /search, /manga или /help.",
            )
