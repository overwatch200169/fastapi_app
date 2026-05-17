from datetime import datetime, timezone
from typing import Optional, Annotated

from elasticsearch.dsl import async_connections,  Q
from fastapi import APIRouter, HTTPException, Query,logger

from app.core.config import settings
from app.models import Article
from app.schemas.articles import ArticleSearch

router = APIRouter( tags=["Elasticsearch"])

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
        q: Annotated[str|None, Query()]=None,
        author_id: Optional[int] = None,
        tags:Annotated[list[str]|None,Query()]=None,
        alive: Annotated[bool|None,Query()] = True,
        page: Annotated[int,Query(ge=1)]=1  ,
        size: Annotated[int,Query( ge=1, le=100)] = 10,
        date_year_month:Annotated[str,Query()]=None
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
                fields=["title^3", "body^2","tags"],
                fuzziness="AUTO",
                # operator="or"
            )
            s = s.query(multi_match_q)

        # 过滤条件
        if author_id:
            s = s.filter("term", author_id=author_id)
        if tags:
            # tag_list=[tag.strip() for tag in tags.split(',')]
            for tag in tags:
                print(tag)
                s=s.filter("term",tags=tag)






        if alive:
            s = s.filter("term", alive=alive)


        if date_year_month:

            year_month=date_year_month.split('-')
            if year_month[-1] in ['01','03','05','07','08','10','12']:
                range_query = {
                    'gte': f'{date_year_month}-01T00:00:00',
                    'lte': f'{date_year_month}-31T23:59:59',  # 注意月份天数
                    'format': 'yyyy-MM-dd\'T\'HH:mm:ss'
                }
            elif year_month[-1]=='02':
                range_query = {
                    'gte': f'{date_year_month}-01T00:00:00',
                    'lte': f'{date_year_month}-28T23:59:59',  # 注意月份天数
                    'format': 'yyyy-MM-dd\'T\'HH:mm:ss'
                }
            else:
                range_query = {
                    'gte': f'{date_year_month}-01T00:00:00',
                    'lte': f'{date_year_month}-30T23:59:59',  # 注意月份天数
                    'format': 'yyyy-MM-dd\'T\'HH:mm:ss'
                }


            s=s.filter('range',create_time=range_query)


        # 只搜索已发布的文章

        # s = s.filter("term", alive=True)

        # 排序
        s = s.sort("-create_time",'updated_time')

        # 分页
        start = (page - 1) * size
        s = s[start:start + size]

        # 执行搜索
        response = await s.execute()

        # 获取聚合数据（如果需要）
        # 例如：按标签聚合


        return {
            "total": response.hits.total.value,
            "page": page,
            "size": size,
            'ids':[hit._id for hit in response['hits']['hits']],
            "results": [hit.to_dict() for hit in response],
            "suggestions": getattr(response, 'suggest', {})
        }
    except Exception as e:
        print(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")

@router.get('/monthly_aggression')
async def monthly_status():
    s = ArticleSearch.search()
    s.aggs.bucket('articles_per_month',  # 聚合结果的名称
            'date_histogram',      # 聚合类型：日期直方图
            field='create_time',    # 您模型中存储创建时间的字段
            calendar_interval='month',  # 按自然月分组
            format='yyyy-MM',      # 可选：格式化返回的日期键
            time_zone='+08:00'     # 可选：指定时区（例如东八区）
    )
    s=s[:0]
    response=await s.execute()
    monthly_stats = []
    if hasattr(response, 'aggregations'):
        for bucket in response.aggregations.articles_per_month.buckets:
            # bucket.key 是时间戳，bucket.key_as_string 是格式化后的日期
            monthly_stats.append({
                'month': bucket.key_as_string,  # 例如 "2024-01"
                'doc_count': bucket.doc_count  # 该月的文章数量
            })

    return {
        "total": response.hits.total.value,
        'monthly_stats': monthly_stats
    }

@router.post("/create_test")
async def create_article_test(article_data: Article):
    """创建文章（示例）"""
    if settings.is_production:
        raise HTTPException(404,'not found')
    else:
        try:
            # 创建文章文档
            article = ArticleSearch()
            article.article_id=article_data.article_id
            article.title = article_data.title
            article.body = article_data.body
            article.alive = article_data.alive
            article.author_id=article_data.author_id
            article.create_time=datetime.now(timezone.utc)
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

@router.get("/test-es-sync")
async def test_es_sync(es_index=None, doc_id=None):
    # 用你现有的、说搜索不到数据的那个 FastAPI 异步 ES 客户端去精准提人
    try:
        # 这里的 client 就是你 FastAPI 原生正在使用的那个异步对象
        es_client = async_connections.get_connection()
        res = await es_client.get(index=es_index, id=doc_id)
        return {
            "status": "🎉 抓到现行了！数据特么的明明就在里面！",
            "source_data": res["_source"]
        }
    except Exception as e:
        return {"status": f"❌ 居然连原生的异步客户端也提不到它: {e}"}


@router.get("/diagnostic-es")
async def diagnostic_es():
    try:
        es_client = async_connections.get_connection()
        # 1. 让你 FastAPI 信任的异步客户端直接调到底层物理接口
        # 获取当前集群所有的物理索引状态
        indices_res = await es_client.perform_request(
            method="GET",
            path="/_cat/indices",
            params={"format": "json"}  # 让它返回干净的 JSON
        )

        # 2. 获取当前集群所有的别名映射关系
        aliases_res = await es_client.perform_request(
            method="GET",
            path="/_aliases"
        )

        return {
            "🎯 当前集群内存在的所有物理索引": indices_res.body,
            "🔀 当前集群内所有的别名映射": aliases_res.body
        }
    except Exception as e:
        return {"❌ 诊断失败原因": str(e)}