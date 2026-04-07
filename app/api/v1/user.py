from fastapi import APIRouter, HTTPException

from app.models import User
from app.schemas.users import UserPublic, UserCreate
from app.utils.deps import UserServiceDep

router=APIRouter()

@router.post("",response_model=UserPublic)
async def create_user(user:UserCreate,service:UserServiceDep)->User:


    return service.create_user(user)


#返回是列表，response_model 也要是列表
@router.get("",response_model=list[UserPublic])
async def read_users(service:UserServiceDep):

    return service.list_users()





@router.get("/{user_id}",response_model=UserPublic)
async def read_user(user_id:int,service:UserServiceDep):
    user=service.read_user(user_id)
    if not user:
        raise HTTPException(404, 'user not found')
    return user




@router.delete("/{user_id}")
async  def delete_user(user_id:int,service:UserServiceDep):
    return service.delete_user(user_id)

