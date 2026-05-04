from fastapi import APIRouter
from .user import router as user_router
from .article import router as article_router
from .auth import router as auth_router
from .contact import router as contact_router
from.search import router as search_router
from.captcha import router as captcha_router
from.egg import router as egg_router

api_router=APIRouter()

api_router.include_router(user_router,prefix='/users')
api_router.include_router(article_router,prefix='/article')
api_router.include_router(auth_router,prefix='/auth')
api_router.include_router(contact_router,prefix='/contact')
api_router.include_router(search_router,prefix='/search')
api_router.include_router(captcha_router,prefix='/captcha')
api_router.include_router(egg_router,prefix='/egg')
__all__ = ["api_router", "user_router",'article_router','auth_router','search_router','captcha_router','egg_router']