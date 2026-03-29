from datetime import datetime

from peewee import (
    SqliteDatabase, Model,
    IntegerField, CharField, TextField, DateTimeField, FloatField,
)

from config import DB_NAME

db = SqliteDatabase(DB_NAME, pragmas={"journal_mode": "wal"})

class BaseModel(Model):
    class Meta:
        database = db

class UserHistory(BaseModel):
    user_id: int       = IntegerField(index=True)
    username: str      = CharField(max_length=255, null=True)
    command: str       = CharField(max_length=64)
    query: str         = CharField(max_length=512)
    anime_id: int      = IntegerField(null=True)
    anime_title: str   = CharField(max_length=512, null=True)
    anime_title_ru: str = CharField(max_length=512, null=True)
    anime_score: float = FloatField(null=True)
    anime_kind: str    = CharField(max_length=32, null=True)
    anime_episodes: int = IntegerField(null=True)
    anime_image: str   = TextField(null=True)
    anime_url: str     = TextField(null=True)
    created_at: datetime = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "user_history"
