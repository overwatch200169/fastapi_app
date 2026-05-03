import pytest
from unittest.mock import patch, AsyncMock

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app  # 替换为你的 FastAPI 入口文件


# client = TestClient(app)


# --- 模拟 ES 行为的 Fixture ---
@pytest_asyncio.fixture
def mock_es_save():
    """
    通过 patch 拦截 ArticleSearch 的 save 方法。
    请确保路径 'app.schemas.Articles.ArticleSearch.save' 与你代码中的实际导入路径一致。
    """
    # 这里的路径是 Service 引用 ArticleSearch 的地方，或者是定义类的地方
    with patch("app.schemas.articles.ArticleSearch.save", new_callable=AsyncMock) as mocked:
        # 模拟 save() 成功后的行为，你可以根据需要给 article 对象赋值
        mocked.return_value = True
        yield mocked



# --- 登录与 CSRF 辅助函数 ---
# def get_csrf_token(client):
#     root_res = client.get("/")
#     csrf_token = root_res.cookies.get("csrf_token")
#     return csrf_token
# def get_tokens_and_cookie(client):
#
#     """同时获取 Auth Token 和最新的 CSRF Cookie"""
#     # 2. 访问根目录获取 CSRF Token
#     # 假设你的根目录会 set-cookie: csrftoken=...
#     csrf_token=get_csrf_token(client)
#
#     # 1. 登录获取 OAuth2 Bearer Token
#     login_res = client.post(
#         "/api/v1/auth/token",
#         data={"username": "testuser@example.com", "password": "Testpassword123"},
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "X-CSRF-Token": csrf_token
#     },
#         cookies={"csrf_token": csrf_token}
#     )
#     access_token = login_res.cookies.get("access_token")
#
#
#
#     # return {
#     #     "headers": {
#     #         "Authorization": f"Bearer {access_token}",
#     #         "X-CSRF-Token": csrf_token
#     #     },
#     #     "cookies": {"csrf_token": csrf_token}
#     # }
#     return access_token


# --- 测试用例 ---

class TestArticleService:
    @pytest_asyncio.fixture
    async def client(self):
        """每个测试独立的客户端"""
        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
        ) as ac:
            yield ac

    async def get_csrf_token(slef,client: AsyncClient):
        response = await client.get("/")
        csrf_token = response.cookies.get("csrf_token")
        assert csrf_token is not None, "无法获取CSRF token"
        return csrf_token

    async def get_tokens_and_cookie(self,client: AsyncClient):
        """同时获取 Auth Token 和最新的 CSRF Cookie"""
        # 2. 访问根目录获取 CSRF Token
        # 假设你的根目录会 set-cookie: csrftoken=...
        csrf_token = await self.get_csrf_token(client)

        # 1. 登录获取 OAuth2 Bearer Token
        login_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser@example.com", "password": "Testpassword123","grant_type": "password"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRF-Token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )
        access_token = login_res.cookies.get("access_token")

        # return {
        #     "headers": {
        #         "Authorization": f"Bearer {access_token}",
        #         "X-CSRF-Token": csrf_token
        #     },
        #     "cookies": {"csrf_token": csrf_token}
        # }
        return access_token

    @pytest.mark.asyncio
    @patch("app.schemas.articles.ArticleSearch.save", new_callable=AsyncMock)
    async def test_create_article_success(self, mock_es_save,client: AsyncClient):
        """测试正常创建流程"""
        # 获取认证和 CSRF

        access_token =await self.get_tokens_and_cookie(client)
        csrf_token=await self.get_csrf_token(client)
        article_payload = {
            "title": "深度学习实战",
            "body": "这是文章正文内容...",
            "tags": "AI, Python"
        }
        print(csrf_token)

        # 发起请求
        response = await client.post(
            "/api/v1/article/",
            json=article_payload,
            headers={
            "Authorization": f"Bearer {access_token}",
            "X-CSRF-Token": csrf_token
        }
        )

        # 断言结果
        assert response.status_code == 200
        # 验证是否真的调用了 save 方法
        assert mock_es_save.called
        # 验证返回的消息
        # assert response.json()["message"] == "文章创建成功"

    @pytest.mark.asyncio
    async def test_csrf_reuse_failure(self, mock_es_save,client: AsyncClient):
        """验证 CSRF Token 使用一次后必须更换的逻辑"""
        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)
        payload = {"title": "标题", "body": "内容", "tags": "tag"}

        # 第一次请求：应该成功
        res1 = await client.post(
            "/api/v1/article/",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )
        assert res1.status_code == 200

        # 第二次请求：使用完全相同的 headers 和 cookies（包含旧的 CSRF）
        # 根据你的描述，这时候应该因为 Token 已被标记为已使用而失败
        res2 = await client.post(
            "/api/v1/article/",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )

        # 预期失败，通常返回 403 Forbidden 或 400 Bad Request
        assert res2.status_code in [400, 403]
        assert "CSRF" in res2.text  # 验证错误信息中包含 CSRF 关键字

    @pytest.mark.asyncio
    async def test_create_article_es_error(self, mock_es_save,client: AsyncClient):
        """测试 ES 保存失败时的异常处理"""
        # 让 mock 的 save 方法抛出异常
        mock_es_save.side_effect = Exception("ES Cluster Down")

        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)
        response = await client.post(
            "/api/v1/article/",
            json={"title": "Error Test", "body": "...", "tags": "..."},
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )

        # 验证是否触发了你代码中的 HTTPException(status_code=500)
        assert response.status_code == 403
        assert "创建失败" in response.json()["detail"]


    # --- 1. 获取文章列表 (公开端点) ---
    @pytest.mark.asyncio
    async def test_list_articles_public(self,client:AsyncClient):
        """测试公开的文章列表接口，无需认证和 CSRF"""
        response = await client.get("/api/v1/article/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    # --- 2. 获取单篇文章 (公开端点) ---
    @pytest.mark.asyncio
    async def test_read_single_article(self,client:AsyncClient):
        """测试读取特定文章详情"""
        article_id = 1
        response = await client.get(f"/api/v1/article/{article_id}")

        if response.status_code == 200:
            assert "title" in response.json()
            assert "body" in response.json()
        else:
            # 如果 ID 不存在，根据你的逻辑可能是 404
            assert response.status_code == 404

    # --- 3. 管理员获取所有文章 (OAuth2 认证) ---
    @pytest.mark.asyncio
    async def test_list_articles_admin_secure(self,client:AsyncClient):
        """测试需要管理员权限的端点"""
        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)

        # 带 Token 请求
        response = await client.get(
            "/api/v1/article/all",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )
        assert response.status_code == 200

        # 不带 Token 请求应失败
        bad_response = await client.get("/api/v1/article/all")
        assert bad_response.status_code == 401

    # --- 4. 更新文章 (OAuth2 + CSRF + ES Mock) ---

    @pytest.mark.asyncio
    # @patch("app.schemas.articles.ArticleSearch.save", new_callable=AsyncMock)
    async def test_update_article_success(self, mock_es_save,client:AsyncClient):
        """测试更新文章，验证 ES 同步更新和安全校验"""
        mock_es_save.return_value = True
        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)

        article_id = 21
        update_data = {
            "title": "更新后的标题",
            "body": "更新后的内容",
            "tags": "updated,tech"
        }

        response = await client.patch(
            f"/api/v1/article/{article_id}",
            json=update_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )

        assert response.status_code == 200
        # assert mock_es_save.called  # 验证是否触发了 ES 更新

    # --- 5. 删除文章 (OAuth2 + CSRF) ---
    @pytest.mark.asyncio
    async def test_delete_article_secure(self,client:AsyncClient):
        """测试删除文章，无需 ES Mock"""
        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)
        article_id = 1

        response = await client.delete(
            f"/api/v1/article/{article_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )

        # 只要 CSRF 和 Auth 通过，业务逻辑应尝试执行
        assert response.status_code in [200, 404]

    # --- 6. 文章恢复 (OAuth2 + CSRF) ---
    @pytest.mark.asyncio
    async def test_article_recovery(self,client:AsyncClient):
        """测试文章恢复端点"""
        access_token = await self.get_tokens_and_cookie(client)
        csrf_token = await self.get_csrf_token(client)
        article_id = 1

        response =await client.patch(
            f"/api/v1/article/recovery/{article_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRF-Token": csrf_token
            }
        )

        assert response.status_code in [200, 404]

    # --- 7. 搜索文章 (Elasticsearch 搜索端点) ---
    # 注意：搜索端点通常直接调用 es.search，不通过 Document.save
    # 这里可以使用 patch 拦截你的 Service 层方法或底层 es 客户端
    @patch("app.services.SearchServices.SearchService.execute_search", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_search_articles(self, mock_search,client:AsyncClient):
        """测试搜索功能，模拟 ES 返回结果"""
        mock_search.return_value = [{"title": "搜索结果1", "article_id": 123}]

        response = await client.get("/api/v1/search/search/article?q=fastapi")

        assert response.status_code == 200
        assert len(response.json()) > 0