# # tests/conftest.py
# import pytest
# import pytest_asyncio
# from httpx import AsyncClient, ASGITransport
# import fakeredis.aioredis
# import fakeredis
# import sys
# import os
# from typing import AsyncGenerator
# from unittest.mock import AsyncMock
#
# # 添加项目根目录到 Python 路径
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#
# from app.main import app
#
#
# @pytest_asyncio.fixture
# async def async_redis_mock():
#     """异步 Redis mock 夹具"""
#     server = fakeredis.aioredis.FakeServer()
#     redis_mock = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
#
#     # 在测试前设置一些初始数据（可选）
#     await redis_mock.set("test_key", "test_value")
#
#     yield redis_mock
#
#     # 清理
#     await redis_mock.close()
#
#
# @pytest_asyncio.fixture(autouse=True)
# async def setup_app_state(async_redis_mock):
#     """
#     自动在每个异步测试前设置 app.state.redis
#     测试后清理
#     """
#     # 保存原始 redis
#     original_redis = None
#     if hasattr(app.state, 'redis'):
#         original_redis = app.state.redis
#
#     # 设置模拟的 Redis
#     app.state.redis = async_redis_mock
#
#     yield
#
#     # 恢复原始 redis
#     if original_redis is not None:
#         app.state.redis = original_redis
#     elif hasattr(app.state, 'redis'):
#         delattr(app.state, 'redis')
#
#
# @pytest_asyncio.fixture
# async def async_client() -> AsyncGenerator[AsyncClient, None]:
#     """
#     提供异步测试客户端
#     使用 ASGITransport 连接到 FastAPI 应用
#     """
#     # 创建使用 ASGI 传输的异步客户端
#     async with AsyncClient(
#             transport=ASGITransport(app=app),  # 关键：使用 ASGITransport
#             base_url="http://test"
#     ) as ac:
#         yield ac
#
#
# @pytest.fixture
# def sync_redis_mock():
#     """同步 Redis mock 夹具（向后兼容）"""
#     return fakeredis.FakeStrictRedis(decode_responses=True)
#
#
# @pytest_asyncio.fixture
# async def auth_headers(async_client: AsyncClient):
#     """
#     获取用于认证的请求头。
#     此夹具会：
#     1. 获取一个CSRF token。
#     2. 使用测试用户凭据调用 `/api/v1/auth/token` 获取访问令牌。
#     3. 返回一个包含 Authorization 和 X-CSRF-Token 的 headers 字典。
#
#     注意：您需要确保数据库中存在此测试用户。
#     """
#     # 1. 获取CSRF Token (用于后续的认证请求)
#     csrf_token = await _get_csrf_token_async(async_client)
#
#     # 2. 准备OAuth2密码授权请求数据
#     # 请将用户名和密码替换为您的测试用户凭据
#     login_data = {
#         "username": "string1@123.com",  # 您的测试用户名
#         "password": "string1",  # 您的测试用户密码
#         "grant_type": "password"
#     }
#
#     # 3. 发送登录请求，获取access_token
#     # 注意：认证端点本身可能需要CSRF保护。根据您的中间件设置调整。
#     login_response = await async_client.post(
#         "/api/v1/auth/token",
#         data=login_data,  # 使用 data 而不是 json，因为内容是 application/x-www-form-urlencoded
#         headers={
#             "Content-Type": "application/x-www-form-urlencoded",
#             "X-CSRF-Token": csrf_token
#         }
#     )
#
#     # 确保登录成功
#     assert login_response.status_code == 200, f"认证失败: {login_response.text}"
#     token_data = login_response.json()
#     access_token = token_data.get("access_token")
#     assert access_token is not None, "响应中未找到 access_token"
#
#     # 4. 获取一个新的CSRF Token (用于接下来的业务请求，因为之前的已使用)
#     new_csrf_token = await _get_csrf_token_async(async_client)
#
#     # 5. 返回组装好的请求头
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "X-CSRF-Token": new_csrf_token
#     }
#     return headers
#
#
# async def _get_csrf_token_async(client: AsyncClient) -> str:
#     """辅助函数：获取CSRF token"""
#     response = await client.get("/")
#     csrf_token = response.cookies.get("csrf_token")
#     assert csrf_token is not None, "无法获取CSRF token"
#     return csrf_token
#
# @pytest.fixture
# def client():
#     """同步测试客户端夹具"""
#     from fastapi.testclient import TestClient
#     with TestClient(app) as tc:
#         yield tc
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import fakeredis.aioredis
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import importlib

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 在导入应用之前，先设置环境变量来禁用Elasticsearch连接
os.environ['TEST_MODE'] = 'true'

from app.main import app


# 模拟Elasticsearch的辅助函数
def mock_elasticsearch():
    """
    模拟Elasticsearch客户端
    使用elasticmock或直接使用MagicMock
    """
    try:
        from elasticmock import elasticmock
        # 如果安装了elasticmock，使用它
        with elasticmock():
            from elasticsearch import Elasticsearch
            es_mock = Elasticsearch()
            return es_mock
    except ImportError:
        # 如果没有安装elasticmock，使用MagicMock
        es_mock = MagicMock()

        # 模拟常用方法
        es_mock.index = MagicMock(return_value={'_id': 'test_id', 'result': 'created'})
        es_mock.get = MagicMock(return_value={'_id': 'test_id', '_source': {}, 'found': True})
        es_mock.search = MagicMock(return_value={'hits': {'hits': [], 'total': {'value': 0}}})
        es_mock.update = MagicMock(return_value={'_id': 'test_id', 'result': 'updated'})
        es_mock.delete = MagicMock(return_value={'_id': 'test_id', 'result': 'deleted'})
        es_mock.exists = MagicMock(return_value=False)
        es_mock.bulk = MagicMock(return_value={'errors': False, 'items': []})
        es_mock.indices = MagicMock()
        es_mock.indices.create = MagicMock(return_value={'acknowledged': True})
        es_mock.indices.exists = MagicMock(return_value=False)
        es_mock.indices.delete = MagicMock(return_value={'acknowledged': True})

        return es_mock


# 模拟异步Elasticsearch客户端
def mock_async_elasticsearch():
    """模拟异步Elasticsearch客户端（如果使用elasticsearch-async）"""
    es_mock = AsyncMock()

    # 模拟异步方法
    es_mock.index = AsyncMock(return_value={'_id': 'test_id', 'result': 'created'})
    es_mock.get = AsyncMock(return_value={'_id': 'test_id', '_source': {}, 'found': True})
    es_mock.search = AsyncMock(return_value={'hits': {'hits': [], 'total': {'value': 0}}})
    es_mock.update = AsyncMock(return_value={'_id': 'test_id', 'result': 'updated'})
    es_mock.delete = AsyncMock(return_value={'_id': 'test_id', 'result': 'deleted'})
    es_mock.exists = AsyncMock(return_value=False)
    es_mock.bulk = AsyncMock(return_value={'errors': False, 'items': []})

    # 模拟indices属性
    es_mock.indices = AsyncMock()
    es_mock.indices.create = AsyncMock(return_value={'acknowledged': True})
    es_mock.indices.exists = AsyncMock(return_value=False)
    es_mock.indices.delete = AsyncMock(return_value={'acknowledged': True})

    return es_mock


@pytest_asyncio.fixture
async def async_redis_mock():
    """异步 Redis mock 夹具"""
    server = fakeredis.aioredis.FakeServer()
    redis_mock = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)

    # 在测试前设置一些初始数据（可选）
    await redis_mock.set("test_key", "test_value")

    yield redis_mock

    # 清理
    await redis_mock.close()


@pytest_asyncio.fixture
async def elasticsearch_mock():
    """
    Elasticsearch mock 夹具
    返回一个模拟的Elasticsearch客户端
    """
    # 根据您的应用使用同步还是异步客户端选择
    # 如果使用同步客户端：
    es_mock = mock_elasticsearch()
    # 如果使用异步客户端：
    # es_mock = mock_async_elasticsearch()

    return es_mock


@pytest_asyncio.fixture(autouse=True)
async def setup_app_state(async_redis_mock, elasticsearch_mock):
    """
    自动在每个异步测试前设置 app.state
    包括Redis和Elasticsearch
    """
    # 保存原始状态
    original_state = {}
    for attr in ['redis', 'es', 'elasticsearch', 'es_client']:  # 常见的属性名
        if hasattr(app.state, attr):
            original_state[attr] = getattr(app.state, attr)

    # 设置模拟的Redis
    app.state.redis = async_redis_mock

    # 设置模拟的Elasticsearch
    # 根据您的应用实际使用的属性名设置
    if hasattr(app.state, 'es'):
        app.state.es = elasticsearch_mock
    elif hasattr(app.state, 'elasticsearch'):
        app.state.elasticsearch = elasticsearch_mock
    elif hasattr(app.state, 'es_client'):
        app.state.es_client = elasticsearch_mock
    else:
        # 如果没有预设属性，我们创建一个
        app.state.es = elasticsearch_mock

    # 设置测试模式标志
    app.state.testing = True

    print(f"测试前: 已设置模拟Redis和Elasticsearch")

    yield

    # 恢复原始状态
    for attr, value in original_state.items():
        setattr(app.state, attr, value)

    # 清理测试期间添加但原来不存在的属性
    for attr in ['redis', 'es', 'elasticsearch', 'es_client', 'testing']:
        if hasattr(app.state, attr) and attr not in original_state:
            delattr(app.state, attr)

    print(f"测试后: 已清理状态")


@pytest_asyncio.fixture
async def async_client():
    """
    提供异步测试客户端
    使用 ASGITransport 连接到 FastAPI 应用
    """
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac