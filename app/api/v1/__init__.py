from fastapi import APIRouter
from .user import router as user_router
from .article import router as article_router
from .auth import router as auth_router

api_router=APIRouter()

api_router.include_router(user_router,prefix='/users')
api_router.include_router(article_router,prefix='/article')
api_router.include_router(auth_router,prefix='/auth')

__all__ = ["api_router", "user_router",'article_router','auth_router']