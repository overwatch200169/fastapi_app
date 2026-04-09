from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, UploadFile

from app.models import User
from app.schemas.users import UserPublic, UserCreate, UserProfilePublic, UserProfileUpdate
# from app.utils.deps import UserServiceDep, get_current_active_user
from app.dependencies.user import UserServiceDep
from app.dependencies.auth import get_current_active_user_dep

router=APIRouter()
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
async  def delete_user(user_id:int,service:UserServiceDep):
    return service.delete_user(user_id)




@router.get('/{user_id}/profile',response_model=UserProfilePublic)
async def read_user_profile(user_id:int,service:UserServiceDep):
    user_profile=service.read_user_profile(user_id)
    if not user_profile:
        raise HTTPException(404,"user profile lost")
    return user_profile

@router.patch('/{user_id}/profile',response_model=UserProfilePublic)
async def update_user_profile(user_id:int,profile:UserProfileUpdate,service:UserServiceDep):
    user = service.read_user(user_id)
    if not user:
        raise HTTPException(404, 'user not found')
    user_profile= service.update_user_profile(user.user_id,profile)
    if not user_profile:
        raise HTTPException(404, 'user profile not found')
    return user_profile

# TODO 上传头像路由
@router.post('/avatar')
async def upload_avatar(current_user:get_current_active_user_dep,user:UserServiceDep,file:UploadFile):
    pass
