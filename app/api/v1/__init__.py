from fastapi import APIRouter
from .user import router as user_router
from .article import router as article_router

api_router=APIRouter()

api_router.include_router(user_router,prefix='/users')
api_router.include_router(article_router,prefix='/article')

__all__ = ["api_router", "user_router",'article_router']