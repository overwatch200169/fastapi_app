# tasks/article_sync_task.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session

from app.core.config import settings
from app.models.databases import get_session, engine
from app.services.simple_sync import simple_article_sync
from app.dependencies.database import SessionDep
from app.core.es_client import get_es_connection
import logging

logger = logging.getLogger(__name__)


def start_article_sync_scheduler():
    """启动文章同步定时任务"""
    scheduler = AsyncIOScheduler()

    # 每10分钟执行一次增量同步
    scheduler.add_job(
        run_article_sync,
        IntervalTrigger(minutes=1),
        id='article_incremental_sync',
        name='文章增量同步',
        max_instances=1
    )

    scheduler.start()
    logger.info("文章同步定时任务已启动")


async def run_article_sync():
    """执行文章同步"""
    with Session(engine) as session:
        try:
            # 获取ES客户端
            es_client = await get_es_connection()

            # 执行同步
            result = await simple_article_sync(
                session=session,
                es_client=es_client,
                hours_back=settings.ES_SYNC_TIME,
                use_upsert=True
            )

            logger.info(f"增量同步完成: {result}")
            return result

        except Exception as e:
            logger.error(f"同步失败: {e}", exc_info=True)
            # 异常会自动回滚session
            raise