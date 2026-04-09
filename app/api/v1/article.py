from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.articles import ArticlePublic, ArticleList, ArticleCreate
from app.schemas.users import UserPublic
# from app.utils.deps import ArticleServiceDep, get_current_active_user
from app.dependencies.article import ArticleServiceDep
from app.dependencies.auth import  get_current_active_user_dep

router=APIRouter()

@router.get('/{article_id}',response_model=ArticlePublic)
async def read_article(article_id:int,service:ArticleServiceDep):
    return service.read_article(article_id)

@router.get('/',response_model=list[ArticleList])
async def list_article(service:ArticleServiceDep):
    return service.list_articles()
@router.post('/',response_model=ArticlePublic)
async def create_article(article:ArticleCreate,service:ArticleServiceDep,user:get_current_active_user_dep):
    return service.create_article(article,user)


