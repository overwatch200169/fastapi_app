from typing import Annotated

from fastapi import Query
from sqlmodel import Session, select

from app.models import Article
from app.schemas.articles import ArticleCreate


class ArticleService:

    def __init__(self,session:Session):
        self.session=session

    def list_articles(self,offset:int=0,limit:Annotated[int,Query(le=100)]=100):

        articles=self.session.exec(select(Article).offset(offset).limit(limit)).all()
        return articles

    def read_article(self,article_id:int):
        article=self.session.get(Article,article_id)
        return article

    def create_article(self,article:ArticleCreate,user):
        article_db=Article.model_validate(article)
        article_db.author_id=user.user_id
        self.session.add(article_db)
        self.session.commit()
        self.session.refresh(article_db)
        return article_db






