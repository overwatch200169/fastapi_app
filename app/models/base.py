from datetime import datetime

from pydantic import BaseModel, Field
from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str =Field(min_length=1)
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

class ContactMe(BaseModel):
    sender_name:str| None = None
    sender_email:str| None = None
    mail_text:str| None = None
    captcha_id:str
    captcha_code: str

class CaptchaVerify(BaseModel):
    captcha_code:str
    captcha_id:str

class EsterEggBase(SQLModel):
    name:str
    birthday:datetime
    homepage:str