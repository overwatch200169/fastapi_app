from datetime import datetime, timezone

from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlmodel import Field,Index,Column

from app.models.base import ArticleBase

class Article(ArticleBase,table=True):

    create_time:datetime=Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False)
    updated_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),nullable=False)
    article_id:int |None =Field(default=None,primary_key=True,sa_column_kwargs={"autoincrement": True})
    author_id:int |None =Field(default=None)
    title :str |None  =Field(default=None,max_length=1000)
    body:str|None=Field(default=None,sa_column=Column(MEDIUMTEXT))
    alive:bool=Field(default=True,)
    tags:str|None=Field(default=None,max_length=1000)
# 为复合查询创建索引：先过滤 alive，再按时间倒序
    __table_args__ = (

        Index("idx_article_author_id","author_id"),
        Index("idx_article_updated_time","updated_time"),
        Index("idx_article_create_time","create_time"),
        Index("idx_article_alive", "alive"),
        Index("idx_article_alive_create_time", "alive", "create_time"),

    )
