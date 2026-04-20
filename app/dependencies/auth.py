from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.security import decode_jwt_token, create_access_token
from app.dependencies.database import SessionDep
from app.models import User
from app.models.base import TokenData, Token
from app.schemas.users import UserPublic
from app.services.AuthServices import AuthService


def get_auth_service(session:SessionDep):
    return AuthService(session)

AuthServiceDep=Annotated[AuthService,Depends(get_auth_service)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token",auto_error=False)#要考虑前缀问题，如果把这个作为依赖运行但是不干扰后续其他获取token的方式需要auto_error=False不抛出错误

async def get_token(request:Request,token_from_header: Annotated[str, Depends(oauth2_scheme)]):
    # token=None
    tokens={}
    token=request.cookies.get('access_token')
    refresh_token=request.cookies.get('refresh_token')
    if not token and token_from_header:
        token=token_from_header
    tokens['access']=token
    tokens['refresh']=refresh_token


    return tokens

# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],service:AuthServiceDep):
async def get_current_user(token: Annotated[dict, Depends(get_token)], service: AuthServiceDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # print(token)
        payload = decode_jwt_token(token.get('access'))
        email = payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception

    user = service.get_user_from_db(token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return UserPublic.model_validate(current_user)

get_current_active_user_dep=Annotated[UserPublic,Depends(get_current_active_user)]


async def refresh_access_token(token:Annotated[dict, Depends(get_token)],current_active_user:get_current_active_user_dep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="refresh token expire",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt_token(token.get('refresh'))
        email=payload.get('sub')
        type = payload.get('type')
        if email is None or type !='refresh':
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = current_active_user
    if user.email != email:
        raise credentials_exception
    new_access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(data={"sub": user.email}, expires_delta=new_access_token_expires)

    return new_access_token

refresh_access_token_dep=Annotated[str,Depends(refresh_access_token)]

async def need_admin(current_active_user:get_current_active_user_dep):
    if current_active_user.level!=0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_active_user

need_admin_dep=Annotated[UserPublic,Depends(need_admin)]