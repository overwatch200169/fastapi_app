from datetime import datetime, timezone
from typing import Optional

from elasticsearch.dsl import async_connections, Query, Q
from fastapi import APIRouter, HTTPException, logger

from app.models import Article
from app.schemas.articles import ArticleSearch

router = APIRouter(prefix="/search", tags=["Elasticsearch"])

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


@router.get('/article')
async def search_articles(
        q: Optional[str] = Query(None, description="搜索关键词"),
        author_id: Optional[int] = None,

        alive: Optional[bool] = Query(None, description="状态"),
        page: int = Query(None, ge=1, description="页码"),
        size: int = Query(None, ge=1, le=100, description="每页大小")
):
    """搜索文章"""
    try:
        # 构建搜索查询
        s = ArticleSearch.search()

        # 关键词搜索
        if q:
            # 多字段搜索
            multi_match_q = Q(
                "multi_match",
                query=q,
                fields=["title^3", "body^2"],
                fuzziness="AUTO",
                # operator="or"
            )
            s = s.query(multi_match_q)

        # 过滤条件
        if author_id:
            s = s.filter("term", author_id=author_id)





        if alive:
            s = s.filter("term", alive=alive)

        # 只搜索已发布的文章

        # s = s.filter("term", alive=True)

        # 排序
        s = s.sort("-crate_time")

        # 分页
        start = (page - 1) * size
        s = s[start:start + size]

        # 执行搜索
        response = await s.execute()

        # 获取聚合数据（如果需要）
        # 例如：按标签聚合
        # s.aggs.bucket('tags', 'terms', field='tags.name.keyword')

        return {
            "total": response.hits.total.value,
            "page": page,
            "size": size,
            "results": [hit.to_dict() for hit in response],
            "suggestions": getattr(response, 'suggest', {})
        }
    except Exception as e:
        print(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")



@router.post("/create_test")
async def create_article_test(article_data: Article):
    """创建文章（示例）"""
    try:
        # 创建文章文档
        article = ArticleSearch()
        article.article_id=article_data.article_id
        article.title = article_data.title
        article.body = article_data.body
        article.alive = article_data.alive
        article.author_id=article_data.author_id
        article.crate_time=datetime.now(timezone.utc)
        article.updated_time=datetime.now(timezone.utc)


        # 保存到Elasticsearch
        await article.save()

        return {
            "message": "文章创建成功",
            "id": article.meta.id,
            "article_id": article.article_id
        }
    except Exception as e:
        print(f"创建文章失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")