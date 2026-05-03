from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator, field_validator

from app.models.base import UserBase, UserProfileBase


class UserPublic(UserBase):
    user_id: int
    # email : str
    username:str
    level: int


class UserCreate(UserBase):
    email: EmailStr
    password: str=Field(min_length=8)
    level: int | None

    @field_validator('password')
    def validate_password_strength(cls, v):
        errors = []
        if not any(c.isupper() for c in v):
            errors.append('至少一个大写字母')
        if not any(c.islower() for c in v):
            errors.append('至少一个小写字母')
        if not any(c.isdigit() for c in v):
            errors.append('至少一个数字')

        if errors:
            raise ValueError(f'密码强度不足：需要{"、".join(errors)}')
        return v

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