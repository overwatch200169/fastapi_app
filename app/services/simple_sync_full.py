# services/simple_sync.py
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from sqlmodel import select, Session
from app.models.articles import Article
from app.schemas.articles import ArticleSearch
from .simple_sync import convert_db_to_es_model, upsert_article_search_instances  # 复用上一版的转换和写入逻辑

logger = logging.getLogger(__name__)


async def full_article_sync_by_page(session: Session, es_client, batch_size: int = 1000) -> Dict[str, Any]:
    """
    【全量兜底同步】采用游标分页流式读取 MySQL，防止内存溢出，批量 upsert 到 ES
    """
    logger.info("=== 开始执行全量文章数据对账/兜底同步 ===")

    total_processed = 0
    total_updated = 0
    total_failed = 0
    last_id = 0  # 使用 ID 游标分页，比 OFFSET 效率更高

    while True:
        # 使用基于 ID 的滚动查询：WHERE article_id > last_id ORDER BY article_id ASC
        statement = (
            select(Article)
            .where(Article.article_id > last_id)
            .order_by(Article.article_id)
            .limit(batch_size)
        )

        results = session.exec(statement)
        db_articles = list(results.all())

        if not db_articles:
            # 没数据了，说明全量扫描完毕
            break

        logger.info(f"正在处理全量同步批次：ID > {last_id}，本批次数量: {len(db_articles)}")

        # 1. 内存模型转换
        article_instances = []
        for article in db_articles:
            instance = convert_db_to_es_model(article)
            if instance:
                article_instances.append(instance)

        # 2. 批量推送到 ES
        if article_instances:
            save_result = await upsert_article_search_instances(es_client, article_instances)
            total_updated += save_result.get("updated", 0)
            total_failed += save_result.get("failed", 0)

        total_processed += len(db_articles)

        # 3. 更新游标 ID，以便下一轮往下查
        last_id = db_articles[-1].article_id

    logger.info(
        f"=== 全量兜底同步结束 === 总扫描: {total_processed} 条, 成功同步: {total_updated} 条, 失败: {total_failed} 条")
    return {
        "status": "success" if total_failed == 0 else "partial_success",
        "total_processed": total_processed,
        "updated": total_updated,
        "failed": total_failed
    }