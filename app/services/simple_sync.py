# services/simple_sync.py
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import json

from sqlmodel import Session

from app.dependencies.database import SessionDep
from app.models import Article
from app.schemas.articles import ArticleSearch

logger = logging.getLogger(__name__)


def get_recent_articles(
        session,
        last_sync_time: Optional[datetime] = None,
        hours_back: int = 24
) -> List:
    """
    从数据库获取最近更新的文章
    :param session: 数据库会话
    :param last_sync_time: 上次同步时间，如果为None则使用hours_back
    :param hours_back: 如果没有last_sync_time，则查询最近多少小时的数据
    :return: 文章列表
    """
    from app.models.articles import Article  # 导入您的SQLModel文章模型

    # 计算查询的起始时间
    if last_sync_time is None:
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
    else:
        start_time = last_sync_time

    logger.info(f"查询数据库，起始时间: {start_time}")

    # 查询最近更新或创建的文章
    # 假设您的Article模型有updated_at和created_at字段
    from sqlmodel import select

    statement = select(Article).where(
        (Article.updated_time >= start_time) |
        (Article.crate_time >= start_time)
    ).order_by(Article.crate_time.desc())

    results = session.exec(statement)
    articles = results.all()

    logger.info(f"从数据库查询到 {len(articles)} 篇文章需要同步")
    return articles


async def create_article_search_instance(db_article):
    """
    将 SQLModel Article 转换为 ArticleSearch 并保存到 Elasticsearch

    Args:
        db_article: SQLModel Article 实例

    Returns:
        是否成功保存
    """
    try:
        # 创建 ArticleSearch 实例
        es_article = ArticleSearch()


        es_article.article_id = db_article.article_id
        es_article.title = db_article.title
        es_article.body = db_article.body
        es_article.alive = db_article.alive if hasattr(db_article, 'alive') else True,
        es_article.author_id = db_article.author_id
        es_article.crate_time = db_article.crate_time
        es_article.updated_time=db_article.updated_time

        # 处理时间字段
        if hasattr(db_article, 'crate_time') and db_article.crate_time:
            if isinstance(db_article.crate_time, datetime):
                es_article.crate_time = db_article.crate_time
            else:
                try:
                    es_article.crate_time = datetime.fromisoformat(
                        str(db_article.crate_time).replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    es_article.crate_time = datetime.now(timezone.utc)

        if hasattr(db_article, 'updated_time') and db_article.updated_time:
            if isinstance(db_article.updated_time, datetime):
                es_article.updated_time = db_article.updated_time
            else:
                try:
                    es_article.updated_time = datetime.fromisoformat(
                        str(db_article.updated_time).replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    es_article.updated_time = datetime.now(timezone.utc)
        # 保存到 Elasticsearch


        print(f"文章已同步到ES: ID={db_article.article_id}")
        return es_article

    except Exception as e:
        logger.error(f"保存文章到ES失败 ID={getattr(db_article, 'article_id', 'unknown')}: {e}")
        return False


async def batch_create_article_search_instances(
        db_articles: list
) -> list:
    """
    批量转换文章为 ArticleSearch 实例（不保存）

    Args:
        db_articles: SQLModel Article 实例列表

    Returns:
        ArticleSearch 实例列表
    """
    instances = []

    for article in db_articles:
        try:
            instance = await create_article_search_instance(article)
            instances.append(instance)

        except Exception as e:
            logger.error(f"转换文章失败 ID={getattr(article, 'article_id', 'unknown')}: {e}")
            continue

    logger.info(f"批量转换完成: {len(instances)}/{len(db_articles)} 篇文章")
    return instances


async def upsert_article_search_instances(
        es_client,
        article_instances: list
) -> Dict[str, Any]:
    """
    使用 upsert 方式批量保存 ArticleSearch 实例
    （如果存在则更新，不存在则创建）

    Args:
        es_client: Elasticsearch 客户端
        article_instances: ArticleSearch 实例列表

    Returns:
        保存结果统计
    """
    from elasticsearch.helpers import async_bulk

    if not article_instances:
        logger.info("没有文章实例需要保存")
        return {"indexed": 0, "failed": 0}

    # 准备批量 upsert 操作
    actions = []
    for instance in article_instances:
        # 获取文档ID
        doc_id = instance.meta.id if hasattr(instance.meta, 'id') else str(instance.article_id)

        # 构建 upsert 操作
        action = {
            "_op_type": "update",  # 使用 update 操作
            "_index": ArticleSearch._index._name,
            "_id": doc_id,
            "doc": instance.to_dict(),  # 更新的文档内容
            "doc_as_upsert": True  # 如果不存在则创建
        }
        actions.append(action)

    # 执行批量 upsert
    try:
        success, failed = await async_bulk(
            es_client,
            actions,
            stats_only=True,
            raise_on_error=False
        )

        logger.info(f"批量 upsert 完成: 成功 {success} 条, 失败 {failed} 条")
        return {"updated": success, "failed": failed}

    except Exception as e:
        logger.error(f"批量 upsert 失败: {e}")
        return {"updated": 0, "failed": len(actions), "error": str(e)}


async def simple_article_sync(
        session,
        es_client,
        hours_back: int = 24,
        use_upsert: bool = True
) -> Dict[str, Any]:
    """
    使用模型转换函数的增量同步

    Args:
        session: 数据库会话
        es_client: Elasticsearch 客户端
        hours_back: 同步多少小时内的数据
        use_upsert: 是否使用 upsert 方式

    Returns:
        同步结果
    """
    from sqlmodel import select
    from datetime import datetime, timedelta
    from app.models.articles import Article

    sync_start = datetime.utcnow() - timedelta(hours=hours_back)

    logger.info(f"开始文章同步，时间范围: {sync_start} 到现在")

    try:

        # 查询需要同步的文章
        # statement = select(Article).where(
        #     (Article.crate_time >= sync_start)
        # ).order_by(Article.crate_time.desc())
        #
        # results = session.exec(statement)
        db_articles = get_recent_articles(session)

        logger.info(f"找到 {len(db_articles)} 篇需要同步的文章")

        if not db_articles:
            return {
                "status": "no_changes",
                "count": 0,
                "success": 0,
                "failed": 0
            }

        # 步骤1: 转换为 ArticleSearch 实例
        article_instances = await batch_create_article_search_instances(db_articles)

        # 步骤2: 批量保存到 Elasticsearch
        # if use_upsert:
        save_result = await upsert_article_search_instances(es_client, article_instances)
        result_key = "updated"
        # else:
            # save_result = await save_article_search_instances(es_client, article_instances)
            # result_key = "indexed"

        result = {
            "status": "success" if save_result["failed"] == 0 else "partial_success",
            "total_articles": len(db_articles),
            "converted_instances": len(article_instances),
            result_key: save_result.get(result_key, 0),
            "failed": save_result["failed"],
            "index_name": ArticleSearch._index._name
        }

        if "error" in save_result:
            result["error"] = save_result["error"]

        logger.info(f"同步完成: {result}")
        return result

    except Exception as e:
        logger.error(f"文章同步失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "total_articles": 0,
            "success": 0,
            "failed": 0
        }