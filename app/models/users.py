from datetime import datetime, timezone

from pydantic import field_serializer
# from pydantic import EmailStr
from sqlmodel import SQLModel,Field,Index

from app.models.base import UserBase,UserProfileBase


class User(UserBase,table=True):
    username: str = Field(max_length=255,nullable=False,min_length=1)
    user_id: int | None = Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
    email: str = Field(default=None,max_length=255)
    password: str | None = Field(default=None)
    create_at: datetime=Field(default_factory=lambda:datetime.now(timezone.utc),nullable=False)
    level: int | None
    __table_args__ = (
        Index("idx_user_username", "username",unique=True),
        Index("idx_user_email", "email",unique=True),
    )


class UserProfile(UserProfileBase,table=True):
    profile_id:int |None = Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
    birthday: datetime | None =Field(default=None)
    age: int | None =Field(default=None)
    bio: str | None =Field(default=None,max_length=255)
    avatar_url: str | None =Field(default=None,max_length=255)