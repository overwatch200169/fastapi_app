from typing import Annotated

from fastapi import Query

from sqlmodel import Session, select

from app.models import User
from app.schemas.users import UserCreate
from app.utils.tools import get_password_hash



class UserService:
    def __init__(self,session:Session):
        self.session=session

    def create_user(self,user:UserCreate)->User:
        db_user=User.model_validate(user)

        hashed_password=get_password_hash(db_user.password)

        db_user.password=hashed_password

        self.session.add(db_user)

        self.session.commit()
        self.session.refresh(db_user)

        return db_user

    def list_users(self, offset: int = 0,limit: Annotated[int, Query(le=100)] = 100, ):
        session = self.session
        users = session.exec(select(User).offset(offset).limit(limit)).all()
        return users

    def read_user(self,user_id:int):
        session = self.session
        user=session.get(User,user_id)


        return user
    def delete_user(self,user_id:int):

        user = self.read_user(user_id)
        if not user:
            return False
        self.session.delete(user)
        self.session.commit()
        return True

