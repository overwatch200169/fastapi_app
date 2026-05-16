from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query

from app.models.base import Page
from app.schemas.articles import ArticlePublic, ArticleList, ArticleCreate, ArticleUpdate
from app.schemas.users import UserPublic
# from app.utils.deps import ArticleServiceDep, get_current_active_user
from app.dependencies.article import ArticleServiceDep
from app.dependencies.auth import get_current_active_user_dep, need_admin_dep

router=APIRouter(tags=['Article'])

@router.get('/all',response_model=Page[ArticleList])
async def list_article_admin(service:ArticleServiceDep,user:need_admin_dep,offset:Optional[int]=Query(None),limit:Optional[int]=Query(None)):
     total,items=service.list_articles(offset=offset,limit=limit,user_level=user.level)
     return{'total':total,'items':items}

@router.get('/{article_id}',response_model=ArticlePublic)
async def read_article(article_id:int,service:ArticleServiceDep):
    article=service.read_article(article_id)
    if not article:
        raise HTTPException(status_code=404,detail="article nor found")
    return article

@router.get('/',response_model=Page[ArticleList])
async def list_article(offset,limit,service:ArticleServiceDep):
    total, items = service.list_articles(offset=offset,limit=limit)
    return {'total': total, 'items': items}



@router.post('/',response_model=ArticlePublic)
async def create_article(article:ArticleCreate,service:ArticleServiceDep,user:get_current_active_user_dep):
    article_data=service.create_article(article, user)
    # try:
    #     await service.create_article_search(article_data)
    # except:
    #     raise HTTPException(status_code=403,detail='add to search fail')
    return article_data

@router.patch('/{article_id}')
async def article_update(article_id, service:ArticleServiceDep, user:get_current_active_user_dep, updated_article:ArticleUpdate):
    update=service.update_article(user_id=user.user_id, article_id=article_id,article=updated_article)
    if not update:
        raise HTTPException (status_code=403,detail='update fail')
    return update

@router.patch('/recovery/{article_id}')
async def article_recovery(article_id, service:ArticleServiceDep, user:need_admin_dep):
    recover=service.recover_article(user_level=user.level, article_id=article_id)
    if not recover:
        raise HTTPException (status_code=403,detail='update fail')
    return recover





@router.delete('/{article_id}')
async def delete_article(article_id,service:ArticleServiceDep,user:get_current_active_user_dep):
    is_removed=service.remove_article(article_id,user.user_id,user.level)

    if not is_removed:
        raise HTTPException(status_code=403,detail='remove fail')
    # else:
    #     await service.delete_article_search_by_id(article_id)
    return is_removed
    # pass


