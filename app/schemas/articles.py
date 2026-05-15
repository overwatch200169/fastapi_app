from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer

from app.models.base import ArticleBase

from elasticsearch.dsl import AsyncDocument, Field, Integer, Keyword, Text, Date, Boolean, Nested


class ArticlePublic(ArticleBase):
    create_time: datetime
    author_id: int | None
    title: str | None
    body: str | None
    tags: str | None

    @field_serializer('create_time')
    def serialize_dt(self, dt: datetime):
        if dt is None:
            return None
        # 如果没有时区信息（Naive），先补上 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # 将 ISO 格式中的 +00:00 替换为 Z
        # 注意：isoformat() 在有位移时默认产生 +00:00
        return dt.isoformat().replace('+00:00', 'Z')

class ArticleList(ArticleBase):
    create_time: datetime
    author_id: int | None
    title: str | None
    article_id:int |None
    tags: str | None
    alive:bool | None

    @field_serializer('create_time')
    def serialize_dt(self, dt: datetime):
        if dt is None:
            return None
        # 如果没有时区信息（Naive），先补上 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # 将 ISO 格式中的 +00:00 替换为 Z
        # 注意：isoformat() 在有位移时默认产生 +00:00
        return dt.isoformat().replace('+00:00', 'Z')

class ArticleCreate(ArticleBase):
    title: str | None
    body: str | None
    tags:str |None

class ArticleUpdate(BaseModel):
    title: str | None =None
    body: str | None =None
    tags: str | None =None

class ArticleSearch(AsyncDocument):
    create_time = Date()
    article_id = Integer()
    author_id = Integer()
    title= Text(analyzer='ik_max_word')
    body = Text(analyzer='ik_max_word')
    alive= Boolean()
    updated_time=Date()
    tags=Keyword(multi=True)

    def to_dict(self, include_meta=False, skip_empty=True):
        # 1. 调用父类原有的转换逻辑得到字典
        d = super().to_dict(include_meta=include_meta, skip_empty=skip_empty)

        # 2. 强制转换日期字段为带 Z 的 ISO 字符串
        # 此时 self.create_time 是 python 的 datetime 对象
        if self.create_time:
            # 如果是 naive 对象（无时区），先补上 UTC
            dt = self.create_time
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            d['create_time'] = dt.isoformat().replace('+00:00', 'Z')

        if self.updated_time:
            dt = self.updated_time
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            d['updated_time'] = dt.isoformat().replace('+00:00', 'Z')

        return d
    class Index:
        name='articles'
