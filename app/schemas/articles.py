from datetime import datetime

from pydantic import BaseModel

from app.models.base import ArticleBase


class ArticlePublic(ArticleBase):
    crate_time: datetime
    author_id: int | None
    title: str | None
    body: str | None

class ArticleList(ArticleBase):
    crate_time: datetime
    author_id: int | None
    title: str | None
    article_id:int |None

class ArticleCreate(ArticleBase):
    title: str | None
    body: str | None

class ArticleUpdate(BaseModel):
    title: str | None =None
    body: str | None =None