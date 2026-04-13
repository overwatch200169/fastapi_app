from elasticsearch.dsl import async_connections
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/elasticsearch", tags=["Elasticsearch"])

@router.get("/health")
async def check_es_connection():
    """
    验证与 Elasticsearch 集群的连接是否健康。
    此端点通过调用集群的 `info()` API 来实现。
    """
    try:
        # 1. 通过 connections 模块，使用在 es_config.py 中创建的 'default' 别名连接
        # 这与文档中“使用别名”和“全局配置”的思路一致。
        # print(f"可用的连接别名: {async_connections.keys()}")
        es_client = async_connections.get_connection()

        # 2. 执行一个最简单的操作：获取集群信息
        # 如果连接成功且集群可访问，此调用会返回集群信息。
        # 如果连接失败（网络问题、认证失败、别名错误），则会抛出异常。
        info = await es_client.info()

        return {
            "status": "connected",
            "cluster_name": info.get('cluster_name'),
            "version": info.get('version', {}).get('number'),
            "message": "成功连接到 Elasticsearch 集群。"
        }
    except Exception as e:
        # 捕获所有可能的异常，如 ConnectionError, AuthenticationException, KeyError（别名不存在）等
        raise HTTPException(
            status_code=503,
            detail={
                "status": "disconnected",
                "error": f"无法连接到 Elasticsearch: {str(e)}"
            }
        )