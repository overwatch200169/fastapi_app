from datetime import datetime, timezone

from sqlmodel import Field

from app.models.base import ArticleBase

class Article(ArticleBase,table=True):
    create_time:datetime=Field(default=datetime.now(timezone.utc))
    updated_time: datetime = Field(default=datetime.now(timezone.utc))
    article_id:int |None =Field(default=None,primary_key=True,index=True)
    author_id:int |None =Field(default=None,index=True)
    title :str |None  =Field(default=None)
    body:str|None=Field(default=None)
    alive:bool=Field(default=True)
    tags:str|None=Field(default=None)

