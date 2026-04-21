from datetime import datetime, timezone

# from pydantic import EmailStr
from sqlmodel import SQLModel,Field

from app.models.base import UserBase,UserProfileBase


class User(UserBase,table=True):
    username: str = Field(index=True,unique=True,max_length=50,nullable=False)
    user_id: int | None = Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
    email: str = Field(default=None, index=True, unique=True,max_length=255)
    password: str | None = Field(default=None, index=True)
    create_at: datetime=Field(default=datetime.now(timezone.utc),nullable=False)
    level: int | None

class UserProfile(UserProfileBase,table=True):
    profile_id:int |None = Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
    birthday: datetime | None =Field(default=None)
    age: int | None =Field(default=None)
    bio: str | None =Field(default=None,max_length=255)
    avatar_url: str | None =Field(default=None,max_length=255)