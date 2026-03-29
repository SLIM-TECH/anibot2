import telebot
from telebot.types import Message

from inline import main_menu


WELCOME = (
    "<b>AniBot 2.0</b> поможет найти аниме и мангу.\n\n"
    "Что умеет:\n"
    "• поиск аниме с подробной карточкой\n"
    "• ссылки на аниме и мангу\n"
    "• выбор озвучки, сезона и серии\n"
    "• отправка лучшего доступного видео или ссылки\n"
    "• попытка отправить PDF для манги, если он есть\n"
)

HELP = (
    "<b>Команды</b>\n"
    "/start - главное меню\n"
    "/help - помощь\n"
    "/search <название> - поиск аниме\n"
    "/manga <название> - поиск манги\n"
    "/top - топ аниме\n"
    "/genre - поиск по жанру\n"
    "/season - подбор по сезону\n"
    "/history - история запросов\n\n"
    "<b>Как смотреть серию</b>\n"
    "1. Открой карточку аниме\n"
    "2. Нажми «🎬 Смотреть»\n"
    "3. Выбери источник и сезон\n"
    "4. Введи номер серии"
)


def register_start_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: Message) -> None:
        name = message.from_user.first_name or "друг"
        bot.send_message(
            message.chat.id,
            f"👋 Привет, <b>{name}</b>!\n\n" + WELCOME,
            reply_markup=main_menu(),
            disable_web_page_preview=True,
        )

    @bot.message_handler(commands=["help"])
    def cmd_help(message: Message) -> None:
        bot.send_message(message.chat.id, HELP, disable_web_page_preview=True)

    @bot.message_handler(func=lambda m: m.text in ("❓ Помощь",))
    def menu_help(message: Message) -> None:
        bot.send_message(message.chat.id, HELP, disable_web_page_preview=True)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() in ("привет", "hi", "hello", "start"))
    def greet(message: Message) -> None:
        name = message.from_user.first_name or "друг"
        bot.send_message(
            message.chat.id,
            f"🎌 Привет, <b>{name}</b>! Нажми /start или используй кнопки меню.",
            reply_markup=main_menu(),
        )
