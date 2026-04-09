from fastapi import FastAPI
from sqlmodel import SQLModel

from . import models
from .api import api_router
from .models.databases import engine

#分模块的时候不能这么做，会循环导入，因为app/main目前是部分初始化
# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

app=FastAPI()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)




@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {'message':'hello world'}