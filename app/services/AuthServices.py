from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import User
from app.utils.tools import verify_password


class AuthService:
    def __init__(self,session:Session):
        self.session=session
    def get_user_from_db(self,email: str):
        session=self.session
        result = session.exec(
            select(User).where(User.email == email)
        )
        user = result.first()
        if not user:
            return False

        return user

    def authenticate_user(self,email:str, password:str):
        print(f"{email}")
        user = self.get_user_from_db(email)
        if not user:
            return False
        if not verify_password(password, user.password):
            return False
        return user




