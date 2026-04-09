from typing import Annotated

from fastapi import Depends

from app.dependencies.database import SessionDep
from app.services.ArticleServices import ArticleService


def get_article_service(session:SessionDep):
    return ArticleService(session)

ArticleServiceDep=Annotated[ArticleService,Depends(get_article_service)]