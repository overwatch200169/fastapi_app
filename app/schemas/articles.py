from datetime import datetime, timezone

from pydantic import BaseModel

from app.models.base import ArticleBase

from elasticsearch.dsl import AsyncDocument, Field, Integer, Keyword, Text, Date, Boolean


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

class ArticleSearch(AsyncDocument):
    crate_time = Date()
    article_id = Integer()
    author_id = Integer()
    title= Text(analyzer='ik_max_word')
    body = Text(analyzer='ik_max_word')
    alive= Boolean()
    updated_time=Date()
    class Index:
        name='articles'
