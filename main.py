import os
import sys

import telebot
from loguru import logger

from config import BOT_TOKEN
from models import db, UserHistory
from start import register_start_handlers
from search import register_search_handlers
from manga import register_manga_handlers
from top import register_top_handlers
from genre import register_genre_handlers
from season import register_season_handlers
from history import register_history_handlers
from unknown import register_unknown_handlers


os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("logs/bot.log", level="DEBUG", rotation="10 MB", serialize=True)


def init_db() -> None:
    db.connect(reuse_if_open=True)
    db.create_tables([UserHistory], safe=True)
    db.close()
    logger.info("База данных инициализирована")


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN не задан. Создай .env и добавь BOT_TOKEN=...")
        sys.exit(1)

    init_db()

    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    logger.info("Регистрируем обработчики...")

    register_start_handlers(bot)
    register_search_handlers(bot)
    register_manga_handlers(bot)
    register_top_handlers(bot)
    register_genre_handlers(bot)
    register_season_handlers(bot)
    register_history_handlers(bot)
    register_unknown_handlers(bot)

    me = bot.get_me()
    logger.info(f"AniBot запущен: @{me.username}")
    bot.infinity_polling(logger_level=None, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
