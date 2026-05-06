from datetime import datetime, timezone

from sqlmodel import Field

from app.models.base import ArticleBase

class Article(ArticleBase,table=True):
    create_time:datetime=Field(default_factory=lambda: datetime.now(timezone.utc),index=True,nullable=False)
    updated_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),index=True,nullable=False)
    article_id:int |None =Field(default=None,primary_key=True,index=True,sa_column_kwargs={"autoincrement": True})
    author_id:int |None =Field(default=None,index=True)
    title :str |None  =Field(default=None,max_length=1000)
    body:str|None=Field(default=None,max_length=2000)
    alive:bool=Field(default=True)
    tags:str|None=Field(default=None,max_length=1000)

