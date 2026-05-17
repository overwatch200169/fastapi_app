import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler

import redis.asyncio as redis
from fastapi import FastAPI
from sqlmodel import SQLModel

from . import models
from .api import api_router
from .core.canal_sync import start_canal_worker, stop_event
from .core.captcha_img import CaptchaManager
from .core.config import settings
from .core.es_client import create_es_connection,get_es_connection
from .core.in_memory_storage import MemoryStorage
from .core.redis_storage import RedisStorage
from .middleware.csrf import CSRFMiddleware
from .models.databases import engine
from .services.es_init import init_es_indexes


#分模块的时候不能这么做，会循环导入，因为app/main目前是部分初始化
# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# app=FastAPI()

project_logger = logging.getLogger("app")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



@asynccontextmanager
async def lifespan(app: FastAPI):
    #日志设置

    error_file_handler=TimedRotatingFileHandler(
        filename=settings.LOG_DIR,
        when='midnight',
        backupCount=30,
        encoding='utf-8'
    )
    project_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    uvicorn_formatter = logging.getLogger("uvicorn").handlers[0].formatter
    console_handler.setFormatter(uvicorn_formatter)

    error_file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    error_file_handler.setFormatter(file_formatter)

    project_logger.addHandler(console_handler)
    project_logger.addHandler(error_file_handler)
    #canal同步任务
    canal_thread = threading.Thread(target=start_canal_worker)
    canal_thread.daemon = True  # 👈 核心绝杀：设置为守护线程！
    canal_thread.start()
    project_logger.info("🚀 Backend Service: Canal Daemon Worker Started.")
    #验证码存储
    storage_type = 'redis' if settings.is_production else 'other'

    if storage_type == "redis":
        redis_client = redis.Redis(host=settings.REDIS_HOST,password=settings.REDIS_PASSWORD,port=settings.REDIS_PORT, decode_responses=True)
        app.state.redis=redis_client
        store = RedisStorage(redis_client)
        project_logger.info("✅ Using Redis Store")
    else:
        store = MemoryStorage()
        project_logger.info("⚠️ Using Memory Store (Dev Only)")
    project_logger.info("创建验证码管理器")
    project_logger.info(store)

    app.state.captcha_manager=CaptchaManager(store)
    #数据库创建
    create_db_and_tables()
    # 启动时：创建Elasticsearch连接
    create_es_connection()
    try:

        es_client = await get_es_connection()
        info = await es_client.info()
        project_logger.info(f"[启动成功] 已连接到 Elasticsearch 集群: {info.get('cluster_name')}, 节点名称: {info['name']}")
        await init_es_indexes(es_client)


    except Exception as e:
        project_logger.error(f"[启动失败] Elasticsearch 连接异常: {e}")
    #全量同步定时任务
    try:
        from app.core.article_sync_task import start_article_sync_scheduler
        start_article_sync_scheduler()
    except Exception as e:
        project_logger.error(f"启动定时任务失败: {e}")
    try:
        from app.core.article_sync_task import run_article_sync
        # 可以立即执行一次，但使用后台任务避免阻塞启动

        asyncio.create_task(run_article_sync())
    except Exception as e:
        project_logger.error(f"初始同步执行失败: {e}")
    yield
    # 关闭时：可以在这里添加清理逻辑，例如关闭所有连接
    # connections.remove_connection('default')

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.shutdown()
        project_logger.info("定时任务已停止")
        del app.state.captcha_manager
        project_logger.info("删除验证码管理器")
    except:
        pass
    project_logger.info("FastAPI 应用关闭。")

# 创建 FastAPI 应用，并注入生命周期
app = FastAPI(lifespan=lifespan,title=settings.PROJECT_NAME,docs_url='/docs' if settings.is_production is False else None)


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()
# 在 FastAPI 中注册
app.add_middleware(CSRFMiddleware,secret_key=settings.SECRET_KEY)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {'message':'hello world'}