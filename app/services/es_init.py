"""
Elasticsearch索引初始化服务
"""
from elasticsearch.dsl import AsyncIndex
from app.schemas.articles import ArticleSearch
# from elasticsearch.dsl import async_connections
import logging

logger = logging.getLogger(__name__)


async def init_es_indexes(es_client,delete_existing = True):
    """
    初始化Elasticsearch索引
    :param delete_existing: 是否删除已存在的索引（用于开发环境）
    """
    print("即将调用 init_es_indexes()")
    try:
        # 获取连接

        es = es_client
        print("已获取Elasticsearch连接")

        # 获取索引对象
        index = AsyncIndex(ArticleSearch._index._name, using='default')
        print(f"索引名称: {index._name}")


        # 检查索引是否存在
        if await index.exists():
            if delete_existing:
                print(f"删除已存在的索引: {index._name}")
                await index.delete()
            else:
                print(f"索引已存在: {index._name}")
                return

        # 创建索引
        print(f"创建索引: {index._name}")

        # 应用映射
        # 注意：Document.init()会创建索引和映射
        await ArticleSearch.init(using='default')

        # 可选：设置索引别名
        # 对应文档中"Index Aliases"部分
        # index.put_alias('articles_current')

        print(f"索引 {index._name} 创建成功")

    except Exception as e:
        logger.error(f"初始化Elasticsearch索引失败: {e}")
        raise


async def update_article_mapping():
    """
    更新文章映射（当字段有变更时）
    注意：这不会删除现有数据，但新字段可能不会被正确索引
    """
    try:
        # 获取文章索引
        index = AsyncIndex(ArticleSearch._index._name, using='default')

        if not await index.exists():
            logger.warning(f"索引不存在: {index._name}")
            return

        # 更新映射
        # 注意：对于已存在的字段，Elasticsearch可能不会更新映射
        # 需要创建新索引并重新索引数据
        logger.info(f"尝试更新索引映射: {index._name}")

        # 这里只是简单记录，实际生产环境需要更复杂的迁移策略
        # 可以参考文档中的"Updating an existing mapping"部分

    except Exception as e:
        logger.error(f"更新映射失败: {e}")
        raise