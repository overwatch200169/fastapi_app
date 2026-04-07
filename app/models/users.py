from datetime import datetime, timezone

from sqlmodel import SQLModel,Field

from app.models.base import UserBase


class User(UserBase,table=True):
    username: str = Field(index=True,unique=True)
    user_id: int | None = Field(default=None, primary_key=True)
    email: str = Field(default=None, index=True, unique=True)
    password: str | None = Field(default=None, index=True)
    create_at: datetime=Field(default=datetime.now(timezone.utc))
    level: int | None
