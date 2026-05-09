from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException,Response
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.models.base import Token
# from app.utils.deps import AuthServiceDep
# from app.utils.tools import create_access_token
from app.dependencies.auth import AuthServiceDep, refresh_access_token_dep
from app.core.security import create_access_token,create_refresh_token

router=APIRouter(tags= ['Authorization'])


@router.post('/token')
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],service:AuthServiceDep,response:Response)->Token:
    user=service.authenticate_user(form_data.username,form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password",headers={"WWW-Authenticate": "Bearer"},)
    access_token_expires=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=create_access_token(data={"sub":user.email},expires_delta=access_token_expires)

    response.set_cookie(key='access_token',value=access_token,samesite='lax',httponly=True,max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60)


    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE)
    refresh_token = create_refresh_token(data={"sub": user.email}, expires_delta=refresh_token_expires)
    response.set_cookie(key='refresh_token', value=refresh_token, samesite='strict', httponly=True,
                        max_age=settings.REFRESH_TOKEN_EXPIRE * 60* 60*24)
    return Token(access_token=access_token,token_type='bearer')

@router.post('/refresh_token')
async def access_token_refresh(refresh_access_token:refresh_access_token_dep,response:Response):

    new_access_token= refresh_access_token
    response.set_cookie(key='access_token',value=new_access_token,samesite='lax',httponly=True,max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60)

    return Token(access_token=new_access_token,token_type='bearer')

#csrf 端点
@router.get('/csrf')
async def get_csrf():
    return{'message':'you get a csrf token'}