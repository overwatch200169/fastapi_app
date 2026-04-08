from typing import Annotated

from fastapi import Depends, Path
from sqlmodel import Session

from app.models.databases import get_session

from app.services.ArticleServices import ArticleService

from app.services.UserServices import UserService



SessionDep = Annotated[Session, Depends(get_session)]


def get_user_service(session: SessionDep) -> UserService:

    return UserService(session)

UserServiceDep=Annotated[UserService,Depends(get_user_service)]

def get_article_service(session:SessionDep):
    return ArticleService(session)

ArticleServiceDep=Annotated[ArticleService,Depends(get_article_service)]

