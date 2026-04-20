from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST
import re
import secrets
import hmac
import time
from hashlib import sha256
from typing import Set, Optional


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 防护中间件"""

    def __init__(
            self,
            app,
            secret_key: str,
            cookie_name: str = "csrf_token",
            header_name: str = "X-CSRF-Token",
            exempt_paths: Optional[list] = None,
            exempt_user_agents: Optional[list] = None,
            max_age: int = 3600
    ):
        super().__init__(app)
        self.secret_key = secret_key.encode()
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.max_age = max_age
        self.used_tokens: Set[str] = set()

        # 默认豁免的路径
        self.exempt_paths = exempt_paths or [
            r"^/docs$",
            r"^/redoc$",
            r"^/openapi\.json$",
            r"^/health$",
        ]
        self.exempt_user_agents = exempt_user_agents or [
            "postman",  # Postman
            "insomnia",  # Insomnia
            "curl",  # curl
            "python-requests",  # Python requests
            "httpclient",  # 其他 HTTP 客户端
        ]

        # 需要 CSRF 保护的方法
        self.protected_methods = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # 检查是否需要 CSRF 保护
        if not self._requires_csrf_protection(request):
            response = await call_next(request)

            # 为 GET 请求设置 CSRF Cookie
            if request.method == "GET":
                self._set_csrf_cookie(response, request)

            return response

        # 获取 Token
        csrf_cookie = request.cookies.get(self.cookie_name)
        csrf_header = request.headers.get(self.header_name)

        # 验证 Token
        if not self._verify_csrf_token(csrf_cookie, csrf_header):
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token verification failed"}
            )

        # 调用下一个中间件或路由
        response = await call_next(request)

        return response

    def _requires_csrf_protection(self, request: Request) -> bool:
        """检查是否需要 CSRF 保护"""
        # 只保护指定的方法
        if request.method not in self.protected_methods:
            return False

        # 检查是否在豁免列表中
        path = request.url.path
        for pattern in self.exempt_paths:
            if re.match(pattern, path):
                return False
        # if request.url.path == "/api/v1/auth/token":
        #     return False
        # #检查用户代理（豁免 API 客户端）
        # user_agent = request.headers.get("User-Agent", "").lower()
        # for agent in self.exempt_user_agents:
        #     if agent in user_agent:
        #         return False

        return True

    def _generate_csrf_token(self) -> str:
        """生成 CSRF Token"""
        # 生成随机 Token
        token = secrets.token_urlsafe(32)

        # 添加时间戳
        timestamp = str(int(time.time()))

        # 计算签名
        data = f"{token}:{timestamp}".encode()
        signature = hmac.new(self.secret_key, data, sha256).hexdigest()

        return f"{token}:{timestamp}:{signature}"

    def _verify_csrf_token(
            self,
            cookie_token: Optional[str],
            header_token: Optional[str],

    ) -> bool:
        """验证 CSRF Token"""
        # 两个 Token 都必须存在
        if not cookie_token or not header_token:
            return False

        # 使用恒定时间比较
        if not hmac.compare_digest(cookie_token, header_token):
            return False

        # 验证 Token 格式
        parts = cookie_token.split(":")
        if len(parts) != 3:
            return False

        token, timestamp_str, signature = parts

        # 验证时间戳
        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())

            # 检查是否过期
            if current_time - timestamp > self.max_age:
                return False
        except ValueError:
            return False

        # 验证签名
        data = f"{token}:{timestamp}".encode()
        expected_signature = hmac.new(self.secret_key, data, sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return False

        # 防止重放攻击
        if cookie_token in self.used_tokens:
            return False

        # 标记为已使用
        self.used_tokens.add(cookie_token)

        # 清理过期的 Token
        self._cleanup_used_tokens()

        return True

    def _cleanup_used_tokens(self):
        """清理过期的已使用 Token"""
        current_time = int(time.time())

        # 找出过期的 Token
        expired = set()
        for token in self.used_tokens:
            parts = token.split(":")
            if len(parts) == 3:
                try:
                    timestamp = int(parts[1])
                    if current_time - timestamp > self.max_age:
                        expired.add(token)
                except ValueError:
                    expired.add(token)

        # 移除过期的 Token
        self.used_tokens -= expired

    def _set_csrf_cookie(self, response: Response, request: Request):
        """设置 CSRF Cookie"""
        # 生成新的 Token
        token = self._generate_csrf_token()

        # 设置 Cookie
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=False,  # 允许前端读取
            secure=request.url.scheme == "https",
            samesite="strict",
            max_age=self.max_age,
            path="/"
        )