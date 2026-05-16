# tasks/article_sync_task.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session

from app.core.config import settings
from app.models.databases import get_session, engine
from app.services.simple_sync import simple_article_sync
from app.dependencies.database import SessionDep
from app.core.es_client import get_es_connection
import logging

from app.services.simple_sync_full import full_article_sync_by_page

logger = logging.getLogger(__name__)


def start_article_sync_scheduler():
    """启动文章同步定时任务"""
    scheduler = AsyncIOScheduler()

    # 每10分钟执行一次增量同步
    scheduler.add_job(
        run_article_sync,
        # IntervalTrigger(minutes=1),
        #改为CronTrigger，定点执行
        CronTrigger(hour=3, minute=0),
        id='article_incremental_sync',
        name='文章全量兜底同步',
        max_instances=1,
    replace_existing = True
    )

    scheduler.start()
    # logger.info("文章同步定时任务已启动")
    logger.info("文章【全量兜底】定时任务已启动，设定为每天凌晨 03:00 执行")


async def run_article_sync():
    """执行文章同步"""
    logger.info("定时触发：开始执行每日全量数据同步...")
    with Session(engine) as session:
        try:
            # 获取ES客户端
            es_client = await get_es_connection()

            # 执行同步
            # result = await simple_article_sync(
            #     session=session,
            #     es_client=es_client,
            #     hours_back=settings.ES_SYNC_TIME,
            #     use_upsert=True
            # )
            result = await full_article_sync_by_page(
                session=session,
                es_client=es_client,
                batch_size=1000
            )

            return result

        except Exception as e:
            logger.error(f"全量同步失败: {e}", exc_info=True)
            # 异常会自动回滚session
            raise