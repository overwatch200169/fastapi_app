from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.articles import ArticlePublic, ArticleList, ArticleCreate, ArticleUpdate
from app.schemas.users import UserPublic
# from app.utils.deps import ArticleServiceDep, get_current_active_user
from app.dependencies.article import ArticleServiceDep
from app.dependencies.auth import  get_current_active_user_dep

router=APIRouter(tags=['Article'])

@router.get('/{article_id}',response_model=ArticlePublic)
async def read_article(article_id:int,service:ArticleServiceDep):
    article=service.read_article(article_id)
    if not article:
        raise HTTPException(status_code=404,detail="article nor found")
    return article

@router.get('/',response_model=list[ArticleList])
async def list_article(service:ArticleServiceDep):
    return service.list_articles()
@router.post('/',response_model=ArticlePublic)
async def create_article(article:ArticleCreate,service:ArticleServiceDep,user:get_current_active_user_dep):
    article_data=service.create_article(article, user)
    try:
        await service.create_article_search(article_data)
    except:
        raise HTTPException(status_code=403,detail='add to search fail')
    return article_data

@router.patch('/{article_id}')
async def article_update(article_id, service:ArticleServiceDep, user:get_current_active_user_dep, updated_article:ArticleUpdate):
    update=service.update_article(user_id=user.user_id, article_id=article_id,article=updated_article)
    if not update:
        raise HTTPException (status_code=403,detail='update fail')
    return update





@router.delete('/{article_id}')
async def delete_article(article_id,service:ArticleServiceDep,user:get_current_active_user_dep):
    is_removed=service.remove_article(article_id,user.user_id)
    await service.delete_article_search_by_id(article_id)
    if not is_removed:
        raise HTTPException(status_code=403,detail='remove fail')
    return is_removed
    # pass


