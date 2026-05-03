from types import SimpleNamespace

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user, get_current_active_user, get_token, get_current_active_user_dep
from app.main import app  # 确保指向你的 FastAPI 实例
from app.schemas.users import UserPublic

client = TestClient(app)


class TestAuthEndpoints:

    # --- 辅助方法：获取 CSRF ---
    def get_csrf(self):
        res = client.get("/")
        return {"token": res.cookies.get("csrf_token"), "cookie": res.cookies}

    # --- 1. 测试登录获取 Token (成功) ---
    @patch("app.services.AuthServices.AuthService.authenticate_user")
    def test_login_for_access_token_success(self, mock_auth):
        """测试正常登录流程"""
        # 模拟认证成功，返回一个 User 对象
        # mock_user = MagicMock()
        # mock_user.username = "testuser"
        # mock_auth.return_value = mock_user
        mock_user = SimpleNamespace(
            user_id=1,
            username="testuser",
            email="test@example.com",
            level=1,
            password="hashed_password_string"  # 如果逻辑中需要验证密码
        )
        mock_auth.return_value = mock_user
        # 获取 CSRF
        csrf = self.get_csrf()

        # OAuth2 密码模式要求使用 data (form-data) 而不是 json
        login_data = {
            "username": "testuser",
            "password": "valid_password"
        }

        response = client.post(
            "/api/v1/auth/token",
            data=login_data,
            headers={"X-CSRF-Token": csrf["token"]},
            cookies=csrf["cookie"]
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    # --- 2. 测试登录失败 (凭据错误) ---
    @patch("app.services.AuthServices.AuthService.authenticate_user")
    def test_login_failure(self, mock_auth):
        """测试凭据错误时的返回"""
        # 模拟 AuthService 返回 False (如你代码所示)
        mock_auth.return_value = False

        csrf = self.get_csrf()
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "user", "password": "wrong_password"},
            headers={"X-CSRF-Token": csrf["token"]},
            cookies=csrf["cookie"]
        )

        # 通常返回 401 或 400
        assert response.status_code in [400, 401]

    # --- 3. 测试获取“我”的信息 (受 OAuth2 保护) ---
    def test_read_users_me(self):
        """测试受保护端点 /api/v1/users/me"""
        # 先模拟登录获取 Token
        # (这里为了演示简单，直接用之前获取 token 的逻辑)
        mock_user = SimpleNamespace(
            user_id=1,
            username="testuser",
            email="test@example.com",
            level=1,
            password="hashed_password_string"  # 如果逻辑中需要验证密码
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch("app.services.AuthServices.AuthService.authenticate_user") as mock_auth:
            mock_auth.return_value = mock_user

            csrf = self.get_csrf()
            login_res = client.post(
                "/api/v1/auth/token",
                data={"username": "a", "password": "b"},
                headers={"X-CSRF-Token": csrf["token"]},
                cookies=csrf["cookie"]
            )
            token = login_res.json()["access_token"]

        # 使用 Token 访问受保护接口
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "username" in response.json()

    # --- 4. 测试刷新令牌 (Refresh Token) ---
    @patch("app.dependencies.auth.decode_jwt_token")
    def test_refresh_token_logic(self, mock_decode):
        test_email = "user@example.com"

        # 1. 编写 mock_decode 的返回值
        mock_decode.return_value = {
            "sub": test_email,
            "type": "refresh"
        }

        # 2. 编写模拟的用户对象
        mock_user = SimpleNamespace(user_id=1,
            username="testuser",
            email=test_email,
            level=1,
            password="hashed_password_string"  )

        # 3. 注入依赖
        app.dependency_overrides[get_token] = lambda: {"refresh": "any_string"}
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # 4. 执行请求
            csrf_res = client.get("/")  # 获取 CSRF
            csrf_token = csrf_res.cookies.get("csrf_token")

            response = client.post(
                "/api/v1/auth/refresh_token",
                headers={"Authorization": "Bearer any_string_works_here",
                "X-CSRF-Token": csrf_token},
                cookies={"csrf_token": csrf_token}
            )

            # 5. 断言
            assert response.status_code == 200
            # 验证确实调用了解码函数，且参数是我们传进去的那个字符串
            mock_decode.assert_called_once_with("any_string")

        finally:
            # 6. 清理依赖覆盖，避免影响其他测试
            app.dependency_overrides.clear()
    # --- 5. 安全性边界测试：无认证访问 ---
    def test_access_without_token(self):
        """验证没有 Token 时访问受限接口会被拒绝"""
        # /api/v1/users/me 是受保护的
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    @patch("app.dependencies.auth.decode_jwt_token")  # 注意路径改为你业务所在文件
    def test_refresh_token_expired_or_invalid(self, mock_decode):
        from jwt import InvalidTokenError

        # 模拟 Token 炸了（过期或签名不对）
        mock_decode.side_effect = InvalidTokenError()

        # 覆盖依赖，确保能进到函数里
        app.dependency_overrides[get_token] = lambda: {"refresh": "bad_token"}
        app.dependency_overrides[get_current_active_user_dep] = lambda: SimpleNamespace(email="a@b.com")

        try:
            csrf_res = client.get("/")  # 获取 CSRF
            csrf_token = csrf_res.cookies.get("csrf_token")
            response = client.post("/api/v1/auth/refresh_token", headers={"Authorization": "Bearer fake",
                                                                          "X-CSRF-Token": csrf_token})

            # 预期返回 401
            assert response.status_code == 401
            # 验证是否返回了你定义的错误信息
            # assert response.json()["detail"] == "refresh token expire"
        finally:
            app.dependency_overrides.clear()

    @patch("app.dependencies.auth.decode_jwt_token")
    def test_refresh_token_wrong_type(self, mock_decode):
        # 模拟解密成功，但类型是 access 而非 refresh
        mock_decode.return_value = {"sub": "test@example.com", "type": "access"}

        app.dependency_overrides[get_token] = lambda: {"refresh": "valid_but_wrong_type_token"}
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=1,
            username="testuser",
            email="test@example.com",
            level=1,
            password="hashed_password_string" )

        try:
            csrf_res = client.get("/")  # 获取 CSRF
            csrf_token = csrf_res.cookies.get("csrf_token")
            response = client.post("/api/v1/auth/refresh_token", headers={"Authorization": "Bearer fake",
                                                                          "X-CSRF-Token": csrf_token})
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    @patch("app.dependencies.auth.decode_jwt_token")
    def test_refresh_token_user_mismatch(self, mock_decode):
        # Token 是用户 B 的
        mock_decode.return_value = {"sub": "user_B@example.com", "type": "refresh"}

        # 但当前登录的用户（Access Token 识别出来的）是用户 A
        mock_user_A = SimpleNamespace(user_id=1,
            username="testuser",
            email= "user_A@example.com",
            level=1,
            password="hashed_password_string" )

        app.dependency_overrides[get_token] = lambda: {"refresh": "user_B_token"}
        app.dependency_overrides[get_current_user] = lambda: mock_user_A

        try:
            csrf_res = client.get("/")  # 获取 CSRF
            csrf_token = csrf_res.cookies.get("csrf_token")
            response = client.post("/api/v1/auth/refresh_token", headers={"Authorization": "Bearer fake",
                                                                          "X-CSRF-Token": csrf_token})

            # 即使 Token 没过期、格式正确，但 email 对不上，必须拒绝
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_refresh_token_missing_field(self):
        # 模拟 get_token 返回了空字典，或者没有 refresh 键
        app.dependency_overrides[get_token] = lambda: {}
        app.dependency_overrides[get_current_active_user_dep] = lambda: SimpleNamespace(email="any@b.com")

        try:
            # 当 token.get('refresh') 为 None 时，decode_jwt_token(None) 应该触发错误
            csrf_res = client.get("/")  # 获取 CSRF
            csrf_token = csrf_res.cookies.get("csrf_token")
            response = client.post("/api/v1/auth/refresh_token", headers={"Authorization": "Bearer fake",
                                                                          "X-CSRF-Token": csrf_token})
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()