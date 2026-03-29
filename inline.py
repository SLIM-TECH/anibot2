from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("🔎 Поиск аниме"),
        KeyboardButton("📚 Манга"),
        KeyboardButton("🏆 Топ аниме"),
        KeyboardButton("🎭 По жанру"),
        KeyboardButton("📅 По сезону"),
        KeyboardButton("📜 История"),
        KeyboardButton("❓ Помощь"),
    )
    return kb


def cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb


def count_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=4)
    kb.add(*[InlineKeyboardButton(str(n), callback_data=f"count:{n}") for n in (3, 5, 7, 10)])
    return kb


def anime_card_kb(anime_id: int, shikimori_url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎬 Смотреть", callback_data=f"watchsel:{anime_id}"),
        InlineKeyboardButton("📊 Подробнее", callback_data=f"detail:{anime_id}"),
    )
    kb.add(InlineKeyboardButton("🌐 Страница аниме", url=shikimori_url))
    return kb


def manga_card_kb(manga_id: int, shikimori_url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📄 PDF (если есть)", callback_data=f"mpdf:{manga_id}"),
        InlineKeyboardButton("📖 Читать мангу", url=shikimori_url),
    )
    return kb


def top_kind_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=3)
    items = [
        ("📺 Сериалы", "tv"),
        ("🎬 Фильмы", "movie"),
        ("💿 OVA", "ova"),
        ("🌐 ONA", "ona"),
        ("⭐ Спешлы", "special"),
        ("🎵 Музыка", "music"),
    ]
    kb.add(*[InlineKeyboardButton(label, callback_data=f"topkind:{kind}") for label, kind in items])
    return kb


def genres_kb(genres: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for genre in genres[:24]:
        gid = genre.get("id")
        name = genre.get("russian") or genre.get("name") or str(gid)
        buttons.append(InlineKeyboardButton(name, callback_data=f"genre:{gid}:{name[:20]}"))
    kb.add(*buttons)
    return kb


def season_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🌸 Весна", callback_data="season:spring"),
        InlineKeyboardButton("☀️ Лето", callback_data="season:summer"),
        InlineKeyboardButton("🍂 Осень", callback_data="season:fall"),
        InlineKeyboardButton("❄️ Зима", callback_data="season:winter"),
    )
    return kb


def year_kb(current_year: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=5)
    years = list(range(current_year - 2, current_year + 1))
    kb.add(*[InlineKeyboardButton(str(y), callback_data=f"year:{y}") for y in reversed(years)])
    return kb


def history_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🗑 Очистить историю", callback_data="hist:clear"),
        InlineKeyboardButton("❌ Закрыть", callback_data="hist:close"),
    )
    return kb


def confirm_clear_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data="hist:confirm_clear"),
        InlineKeyboardButton("❌ Отмена", callback_data="hist:cancel_clear"),
    )
    return kb


def source_kb(sources: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for idx, source in enumerate(sources[:10]):
        title = source.get("title") or f"Источник {idx + 1}"
        episodes = source.get("episodes_count")
        suffix = f" · {episodes} эп." if episodes else ""
        kb.add(InlineKeyboardButton(f"{idx + 1}. {title}{suffix}", callback_data=f"vsrc:{idx}"))
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb


def watch_season_kb(source_idx: int, seasons: list[int]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=4)
    for season in seasons[:12]:
        kb.add(InlineKeyboardButton(f"S{season}", callback_data=f"vseason:{source_idx}:{season}"))
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb
