from typing import Annotated

from fastapi import Depends, Path
from sqlmodel import Session

from app.models.databases import get_session
from app.models.users import User
from app.services.UserServices import UserService



SessionDep = Annotated[Session, Depends(get_session)]


def get_user_service(session: SessionDep) -> UserService:

    return UserService(session)

UserServiceDep=Annotated[UserService,Depends(get_user_service)]

