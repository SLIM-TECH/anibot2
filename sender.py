from typing import Optional

import telebot
from telebot.types import InlineKeyboardMarkup

from shikimori import get_image_url, get_shikimori_url, get_shikimori_manga_url
from service import save_history
from inline import anime_card_kb, manga_card_kb
from formatters import format_anime_card, format_manga_card


def send_anime_card(
    bot: telebot.TeleBot,
    chat_id: int,
    anime: dict,
    index: int = 0,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    command: str = "search",
    query: str = "",
) -> None:
    card = format_anime_card(anime, index=index)
    anime_id = anime.get("id")
    url = get_shikimori_url(anime)
    image_url = get_image_url(anime, "original")
    kb = anime_card_kb(anime_id, url)

    _send(bot, chat_id, card, image_url, kb)

    if user_id:
        try:
            score = float(anime.get("score") or 0) or None
        except (ValueError, TypeError):
            score = None
        save_history(
            user_id=user_id,
            username=username,
            command=command,
            query=query,
            anime_id=anime_id,
            anime_title=anime.get("name"),
            anime_title_ru=anime.get("russian"),
            anime_score=score,
            anime_kind=anime.get("kind"),
            anime_episodes=anime.get("episodes") or None,
            anime_image=image_url,
            anime_url=url,
        )


def send_manga_card(
    bot: telebot.TeleBot,
    chat_id: int,
    manga: dict,
    index: int = 0,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    query: str = "",
) -> None:
    card = format_manga_card(manga, index=index)
    manga_id = manga.get("id")
    url = get_shikimori_manga_url(manga)
    image_url = get_image_url(manga, "original")
    kb = manga_card_kb(manga_id, url)

    _send(bot, chat_id, card, image_url, kb)

    if user_id:
        try:
            score = float(manga.get("score") or 0) or None
        except (ValueError, TypeError):
            score = None

        save_history(
            user_id=user_id,
            username=username,
            command="manga",
            query=query,
            anime_id=manga_id,
            anime_title=manga.get("name"),
            anime_title_ru=manga.get("russian"),
            anime_score=score,
            anime_kind=manga.get("kind"),
            anime_episodes=manga.get("chapters") or None,
            anime_image=image_url,
            anime_url=url,
        )


def _send(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    image_url: Optional[str],
    kb: InlineKeyboardMarkup,
) -> None:
    if image_url:
        try:
            bot.send_photo(chat_id, image_url, caption=text, reply_markup=kb)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=kb, disable_web_page_preview=True)
