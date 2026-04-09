from typing import Annotated

from fastapi import Depends

from app.services.UserServices import UserService
from app.dependencies.database import SessionDep


def get_user_service(session: SessionDep) -> UserService:

    return UserService(session)

UserServiceDep=Annotated[UserService,Depends(get_user_service)]