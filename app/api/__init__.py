from .v1 import api_router as v1_router

# 可选：创建一个合并的路由器
from fastapi import APIRouter

# 创建根路由器
api_router = APIRouter()

# 包含所有版本的路由
api_router.include_router(v1_router, prefix="/v1", tags=["v1"])
__all__=["v1_router",'api_router']