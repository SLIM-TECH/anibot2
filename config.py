import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

SHIKIMORI_BASE_URL: str = "https://shikimori.one/api"
SHIKIMORI_HEADERS: dict = {
    "User-Agent": "AniBot/1.0 (Telegram Bot; contact@example.com)",
}

KODIK_TOKEN: str = os.getenv("KODIK_TOKEN", "YOUR_KODIK_TOKEN_HERE")
KODIK_BASE_URL: str = "https://kodikapi.com"
ANILIBRIA_BASE_URL: str = "https://api.anilibria.tv/v3"
ANILIBRIA_FALLBACK_BASE_URLS: list[str] = [
    "https://api.anilibria.tv/v3",
    "https://anilibria.top/api/v1",
]

DEFAULT_LIMIT: int = 5
MAX_LIMIT: int = 10
DB_NAME: str = "anibot.db"
