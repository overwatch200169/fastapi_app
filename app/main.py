from fastapi import FastAPI

from . import models
from .api import api_router
from .models.databases import SQLModel,engine

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