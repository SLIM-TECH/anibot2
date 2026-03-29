from typing import Optional

from loguru import logger
from peewee import PeeweeException

from models import db, UserHistory


def save_history(
    user_id: int,
    username: Optional[str],
    command: str,
    query: str,
    anime_id: Optional[int] = None,
    anime_title: Optional[str] = None,
    anime_title_ru: Optional[str] = None,
    anime_score: Optional[float] = None,
    anime_kind: Optional[str] = None,
    anime_episodes: Optional[int] = None,
    anime_image: Optional[str] = None,
    anime_url: Optional[str] = None,
) -> None:
    try:
        db.connect(reuse_if_open=True)
        UserHistory.create(
            user_id=user_id,
            username=username,
            command=command,
            query=query,
            anime_id=anime_id,
            anime_title=anime_title,
            anime_title_ru=anime_title_ru,
            anime_score=anime_score,
            anime_kind=anime_kind,
            anime_episodes=anime_episodes,
            anime_image=anime_image,
            anime_url=anime_url,
        )
    except PeeweeException as error:
        logger.error(f"save_history error: {error}")
    finally:
        db.close()


def get_history(user_id: int, limit: int = 15) -> list[UserHistory]:
    try:
        db.connect(reuse_if_open=True)
        return list(
            UserHistory.select()
            .where(UserHistory.user_id == user_id)
            .order_by(UserHistory.created_at.desc())
            .limit(limit)
        )
    except PeeweeException as error:
        logger.error(f"get_history error: {error}")
        return []
    finally:
        db.close()


def clear_history(user_id: int) -> int:
    try:
        db.connect(reuse_if_open=True)
        return UserHistory.delete().where(UserHistory.user_id == user_id).execute()
    except PeeweeException as error:
        logger.error(f"clear_history error: {error}")
        return 0
    finally:
        db.close()
