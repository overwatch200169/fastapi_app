from datetime import datetime

from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str
    email: str

class UserProfileBase(SQLModel):
    user_id:int

class ArticleBase(SQLModel):
    title:str