from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from . import models
from .api import api_router
from .core.es_client import create_es_connection,get_es_connection
from .models.databases import engine
from .services.es_init import init_es_indexes


#分模块的时候不能这么做，会循环导入，因为app/main目前是部分初始化
# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# app=FastAPI()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # 启动时：创建Elasticsearch连接
    create_es_connection()
    try:

        es_client = await get_es_connection()
        # info = await es_client.info()
        # print(f"[启动成功] 已连接到 Elasticsearch 集群: {info.get('cluster_name')}")
        await init_es_indexes(es_client)


    except Exception as e:
        print(f"[启动失败] Elasticsearch 连接异常: {e}")
    try:
        from app.core.article_sync_task import start_article_sync_scheduler
        start_article_sync_scheduler()
    except Exception as e:
        print(f"启动定时任务失败: {e}")
    try:
        from app.core.article_sync_task import run_article_sync
        # 可以立即执行一次，但使用后台任务避免阻塞启动
        import asyncio
        asyncio.create_task(run_article_sync())
    except Exception as e:
        print(f"初始同步执行失败: {e}")
    yield
    # 关闭时：可以在这里添加清理逻辑，例如关闭所有连接
    # connections.remove_connection('default')
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.shutdown()
        print("定时任务已停止")
    except:
        pass
    print("FastAPI 应用关闭。")

# 创建 FastAPI 应用，并注入生命周期
app = FastAPI(lifespan=lifespan)


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {'message':'hello world'}