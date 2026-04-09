from typing import Annotated

from fastapi import Depends, Path, HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlmodel import Session

from app.models import User
from app.models.base import TokenData
from app.models.databases import get_session
from app.schemas.users import UserPublic

from app.services.ArticleServices import ArticleService
from app.services.AuthServices import AuthService

from app.services.UserServices import UserService
from app.utils.tools import decode_jwt_token

SessionDep = Annotated[Session, Depends(get_session)]


def get_user_service(session: SessionDep) -> UserService:

    return UserService(session)

UserServiceDep=Annotated[UserService,Depends(get_user_service)]

def get_article_service(session:SessionDep):
    return ArticleService(session)

ArticleServiceDep=Annotated[ArticleService,Depends(get_article_service)]

def get_auth_service(session:SessionDep):
    return AuthService(session)

AuthServiceDep=Annotated[AuthService,Depends(get_auth_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")#要考虑前缀问题

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],service:AuthServiceDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt_token(token)
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