from datetime import datetime

from pydantic import BaseModel

from app.models.base import UserBase, UserProfileBase


class UserPublic(UserBase):
    user_id: int
    # email : str
    username:str

class UserCreate(UserBase):
    email: str | None
    password: str
    level: int | None

class UserProfilePublic(UserProfileBase):
    user_id:int
    birthday: datetime | None
    age: int | None
    bio: str | None
    avatar_url: str | None

class UserProfileUpdate(BaseModel):
    birthday: datetime | None =None
    age: int | None=None
    bio: str | None=None
    avatar_url: str | None=None