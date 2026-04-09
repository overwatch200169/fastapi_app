from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.utils.config import settings
from app.models.base import Token
from app.utils.deps import AuthServiceDep
from app.utils.tools import create_access_token

router=APIRouter()

@router.post('/token')
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],service:AuthServiceDep)->Token:
    user=service.authenticate_user(form_data.username,form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password",headers={"WWW-Authenticate": "Bearer"},)
    access_token_expires=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=create_access_token(data={"sub":user.email},expires_delta=access_token_expires)
    return Token(access_token=access_token,token_type='bearer')