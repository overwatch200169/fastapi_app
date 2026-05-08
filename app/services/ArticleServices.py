from typing import Annotated
from datetime import datetime, timezone
from fastapi import Query, HTTPException
from sqlmodel import Session, select, desc,func

from app.models import Article
from app.schemas.articles import ArticleCreate, ArticleSearch, ArticleUpdate


class ArticleService:

    def __init__(self,session:Session):
        self.session=session

    def list_articles_by_user(self,user_id: int,offset:int=0,limit:int=100):

        articles=self.session.exec(select(Article).where(Article.alive==True).where(Article.author_id==user_id).offset(offset).limit(limit)).all()

        return articles


    def list_articles(self,user_level: int=None,offset:int=0,limit:Annotated[int,Query(le=1000)]=1000):

        if user_level!=0:
            count = self.session.exec(select(func.count(Article.id)).where(Article.alive == True)).one()
            articles=self.session.exec(select(Article).where(Article.alive==True).order_by(desc(Article.create_time)).offset(offset).limit(limit)).all()

        else:
            count = self.session.exec(select(func.count(Article.id))).one()
            articles = self.session.exec(select(Article).order_by(desc(Article.create_time)).offset(offset).limit(limit)).all()
        return count,articles

    def read_article(self,article_id:int):
        article=self.session.get(Article,article_id)
        if not article.alive:
            return False
        return article

    def create_article(self,article:ArticleCreate,user):
        article_db=Article.model_validate(article)
        article_db.author_id=user.user_id
        self.session.add(article_db)
        self.session.commit()
        self.session.refresh(article_db)
        return article_db
    def update_article(self,user_id,article_id,article:ArticleUpdate):

        article_db=self.read_article(article_id)
        if article_db is False:
            return False
        if article_db.author_id==user_id:

            article_data=article.model_dump(exclude_unset=True)

            article_db.sqlmodel_update(article_data)
            article_db.updated_time=datetime.now(timezone.utc)
            self.session.add(article_db)
            self.session.commit()
            self.session.refresh(article_db)
        else:
            return False
        return True

    def remove_article(self, article_id, user_id, user_level=None):
        article_db=self.read_article(article_id)
        if not article_db:
            raise HTTPException(404, "文章不存在")
        article_removal=Article(alive=False)
        try:
            if article_db.author_id==user_id or user_level==0:
                article_data=article_removal.model_dump(exclude_unset=True)
                article_db.sqlmodel_update(article_data)
                self.session.add(article_db)
                self.session.commit()
                self.session.refresh(article_db)
            else:
                raise HTTPException(403, "无权删除此文章")
        except Exception as e:
            return False
        return True

    def recover_article(self, article_id, user_level):
        article_db=self.session.get(Article,article_id)
        if not article_db:
            raise HTTPException(404, "文章不存在")
        article_recovery=Article(alive=True)
        try:
            if user_level==0:
                article_data=article_recovery.model_dump(exclude_unset=True)
                article_db.sqlmodel_update(article_data)
                self.session.add(article_db)
                self.session.commit()
                self.session.refresh(article_db)
            else:
                raise HTTPException(403, "无权恢复此文章")
        except Exception as e:
            return False
        return True


    #TODO es双写双删
    @staticmethod
    async def create_article_search(article_data: Article):

        try:
            # 创建文章文档
            article = ArticleSearch(meta={'id':article_data.article_id})
            # article
            article.article_id=article_data.article_id
            article.title = article_data.title
            article.body = article_data.body
            article.alive = article_data.alive
            article.author_id=article_data.author_id
            article.create_time=article_data.create_time
            article.updated_time=article_data.updated_time
            article.tags = [tag.strip() for tag in article_data.tags.split(',') if tag.strip()]


            # 保存到Elasticsearch
            await article.save()

            return {
                "message": "文章创建成功",
                "id": article.meta.id,
                "article_id": article.article_id
            }
        except Exception as e:
            print(f"创建文章失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

    @staticmethod
    async def delete_article_search_by_id(article_id:int):
        try:
            print(article_id)
            s=ArticleSearch().search()
            s.filter("term", article_id=article_id)
            response=await s.execute()
            print(response[0].article_id)
            print(response[0].alive)
            response[0].alive=False
            await response[0].save()
        except Exception as e:
            print(str(e))
            return False










