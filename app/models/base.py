from datetime import datetime

from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str
    email: str

class UserProfileBase(SQLModel):
    birthday: datetime |None
    age: int |None
    Bio :str|None

