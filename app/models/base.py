from datetime import datetime

from pydantic import BaseModel
from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str
    email: str

class UserProfileBase(SQLModel):
    user_id:int

class ArticleBase(SQLModel):
    title:str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
