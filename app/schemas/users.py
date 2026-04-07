from app.models.base import UserBase


class UserPublic(UserBase):
    user_id: int
    email : str
    username:str

class UserCreate(UserBase):
    email: str | None
    password: str
    level: int | None

