from fastapi import APIRouter

from app.schemas.articles import ArticlePublic, ArticleList, ArticleCreate
from app.utils.deps import ArticleServiceDep

router=APIRouter()

@router.get('/{article_id}',response_model=ArticlePublic)
async def read_article(article_id:int,service:ArticleServiceDep):
    return service.read_article(article_id)

@router.get('/',response_model=list[ArticleList])
async def list_article(service:ArticleServiceDep):
    return service.list_articles()
@router.post('/',response_model=ArticlePublic)
async def create_article(article:ArticleCreate,service:ArticleServiceDep):
    return service.create_article(article)


