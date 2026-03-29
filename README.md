# AniBot 2

Telegram-бот для поиска аниме и манги, истории запросов и просмотра доступных видео-источников.

## Функции

- Поиск аниме (`/search`)
- Поиск манги (`/manga`)
- Топ аниме (`/top`)
- Поиск по жанру (`/genre`)
- Поиск по сезону (`/season`)
- История запросов (`/history`)
- Выбор источника, сезона и серии

## Установка

1. Установи зависимости Python.
2. Создай `.env` и добавь:

```env
BOT_TOKEN=your_telegram_bot_token
KODIK_TOKEN=your_kodik_token
```

`KODIK_TOKEN` необязателен, но без него часть источников может быть недоступна.

## Запуск

```bash
python main.py
```

## Структура

- `main.py` — точка входа
- `search.py` — поиск и логика просмотра
- `manga.py` — поиск манги
- `shikimori.py` — API Shikimori
- `kodik.py` — источники видео и fallback-провайдеры
- `models.py`, `service.py` — история и БД
