from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.articles import ArticlePublic, ArticleList, ArticleCreate
from app.schemas.users import UserPublic
# from app.utils.deps import ArticleServiceDep, get_current_active_user
from app.dependencies.article import ArticleServiceDep
from app.dependencies.auth import  get_current_active_user_dep

router=APIRouter()

@router.get('/{article_id}',response_model=ArticlePublic)
async def read_article(article_id:int,service:ArticleServiceDep):
    article=service.read_article(article_id)
    if not article:
        raise HTTPException(status_code=404,detail="article nor found")
    return

@router.get('/',response_model=list[ArticleList])
async def list_article(service:ArticleServiceDep):
    return service.list_articles()
@router.post('/',response_model=ArticlePublic)
async def create_article(article:ArticleCreate,service:ArticleServiceDep,user:get_current_active_user_dep):
    return service.create_article(article,user)
@router.delete('/{article_id}')
async def delete_article(article_id,service:ArticleServiceDep,user:get_current_active_user_dep):
    is_removed=service.remove_article(article_id,user.user_id)
    if not is_removed:
        raise HTTPException(status_code=403,detail='remove fail')
    return is_removed
    # pass


