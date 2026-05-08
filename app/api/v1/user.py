from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, UploadFile, Query

from app.core.config import settings
from app.dependencies.article import ArticleServiceDep
from app.models import User
from app.schemas.articles import ArticlePublic, ArticleList
from app.schemas.users import UserPublic, UserCreate, UserProfilePublic, UserProfileUpdate
# from app.utils.deps import UserServiceDep, get_current_active_user
from app.dependencies.user import UserServiceDep
from app.dependencies.auth import get_current_active_user_dep, need_admin_dep

router=APIRouter(tags=['User'])
#形参决定了请求体所以在形参中加入profile：UserProfileCreate的时候请求体会检查相关的参数（现在已经被删）
@router.post("",response_model=UserPublic)
async def create_user(user:UserCreate,service:UserServiceDep)->User:


    return service.create_user_with_profile(user)



#返回是列表，response_model 也要是列表
@router.get("",response_model=list[UserPublic])
async def read_users(service:UserServiceDep):

    return service.list_users()


@router.get("/me",response_model=UserPublic)
async def read_users_me(current_user: get_current_active_user_dep):
    return current_user


@router.get("/{user_id}",response_model=UserPublic)
async def read_user(user_id:int,service:UserServiceDep):
    user=service.read_user(user_id)
    if not user:
        raise HTTPException(404, 'user not found')
    return user




@router.delete("/{user_id}")
async  def delete_user(user_id:int,service:UserServiceDep,current_user:need_admin_dep):
    if current_user.level==0:
        return service.delete_user(user_id)
    raise HTTPException(403, "需要管理员权限")




@router.get('/{user_id}/profile',response_model=UserProfilePublic)
async def read_user_profile(user_id:int,service:UserServiceDep):
    user_profile=service.read_user_profile(user_id)
    if not user_profile:
        raise HTTPException(404,"user profile lost")
    return user_profile

@router.get('/{user_id}/article',response_model=list[ArticleList])
async def read_article_by_user(user_id:int,service:ArticleServiceDep,offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),):
    article_by_user=service.list_articles_by_user(user_id,offset,limit)

    return article_by_user


@router.patch('/{user_id}/profile',response_model=UserProfilePublic)
async def update_user_profile(user_id:int,profile:UserProfileUpdate,service:UserServiceDep,current_user:get_current_active_user_dep):
    user = service.read_user(user_id)
    if not user:
        raise HTTPException(404, 'user not found')
    if user_id!=current_user.user_id:
        raise HTTPException(403)
    user_profile= service.update_user_profile(user.user_id,profile)
    if not user_profile:
        raise HTTPException(404, 'user profile not found')
    return user_profile


@router.post('/avatar',response_model=UserProfilePublic)
async def upload_avatar(current_user:get_current_active_user_dep,service:UserServiceDep,file:UploadFile):
    if settings.is_production:
        raise HTTPException(404,'not found')
    else:
        uploaded_avatar_profile=service.update_user_avatar(current_user,file)
        return uploaded_avatar_profile
