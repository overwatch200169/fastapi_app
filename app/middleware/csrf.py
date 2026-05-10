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
from fastapi import Depends,Request


import redis.asyncio as redis




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

    ):
        super().__init__(app)
        self.secret_key = secret_key.encode()
        self.cookie_name = cookie_name
        self.header_name = header_name
        # self.max_age = max_age
        # self.used_tokens: Set[str] = set()

        # 默认豁免的路径
        self.exempt_paths = exempt_paths or [
            r"^/api/v1/auth/token",
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

    # async def dispatch(self, request: Request, call_next) -> Response:
    #     # 检查是否需要 CSRF 保护
    #     if not self._requires_csrf_protection(request):
    #         response = await call_next(request)
    #
    #         # 为 GET 请求设置 CSRF Cookie
    #         if request.method == "GET":
    #             self._set_csrf_cookie(response, request)
    #
    #         return response
    #
    #     # 获取 Token
    #     csrf_cookie = request.cookies.get(self.cookie_name)
    #     csrf_header = request.headers.get(self.header_name)
    #
    #     # 验证 Token
    #     if not self._verify_csrf_token(csrf_cookie, csrf_header):
    #         return JSONResponse(
    #             status_code=HTTP_403_FORBIDDEN,
    #             content={"detail": "CSRF token verification failed"}
    #         )
    #
    #     # 调用下一个中间件或路由
    #     response = await call_next(request)
    #
    #     return response
    async def dispatch(self, request: Request, call_next) -> Response:
        # 为每个请求生成唯一跟踪ID
        client=request.app.state.redis
        import uuid
        if not hasattr(request.state, 'request_trace_id'):
            request.state.request_trace_id = str(uuid.uuid4())[:8]

        trace_id = request.state.request_trace_id
        current_time = time.time()

        print(f"\n{'=' * 60}")
        print(f"[CSRF {trace_id}] 开始处理: {request.method} {request.url.path}")
        print(f"[CSRF {trace_id}] 时间: {current_time}")
        print(f"[CSRF {trace_id}] 请求ID: {id(request)}")  # 内存地址，查看是否是同一个对象

        try:
            # 检查是否需要 CSRF 保护
            if not self._requires_csrf_protection(request):
                response = await call_next(request)
                #所有请求都可以获得token
                await self._set_csrf_cookie(client,response, request)
                print(f"[CSRF {trace_id}] 请求完成: 状态{response.status_code}")
                return response

            # 获取 Token
            csrf_cookie = request.cookies.get(self.cookie_name)
            csrf_header = request.headers.get(self.header_name)

            print(f"[CSRF {trace_id}] 验证Token...")
            verify_result = await self._verify_csrf_token(client,csrf_cookie, csrf_header)

            if not verify_result:
                print(f"[CSRF {trace_id}] 验证失败，返回403")
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"detail": "CSRF token verification failed"}
                )

            print(f"[CSRF {trace_id}] 验证成功，继续处理...")
            response = await call_next(request)
            #业务逻辑执行成功后，生成一个新的Token返回给前端
            # 这样下一次 POST 就能用这个新 Token，实现“阅后即焚”的闭环
            if 200 <= response.status_code < 300:
                await self._set_csrf_cookie(client, response, request)

            print(f"[CSRF {trace_id}] 请求处理完成: 状态{response.status_code}")
            return response

        except Exception as e:
            print(f"[CSRF {trace_id}] 发生异常: {type(e).__name__}: {e}")
            raise
        finally:
            print(f"[CSRF {trace_id}] 中间件退出")
            print(f"{'=' * 60}")

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

    async def _generate_csrf_token(self) -> str:
        """生成 CSRF Token"""
        # 生成随机 Token
        token = secrets.token_urlsafe(32)

        # 添加时间戳
        timestamp = str(int(time.time()))

        # 计算签名
        data = f"{token}:{timestamp}".encode()
        signature = hmac.new(self.secret_key, data, sha256).hexdigest()

        return f"{token}:{timestamp}:{signature}"

    # def _verify_csrf_token(
    #         self,
    #         cookie_token: Optional[str],
    #         header_token: Optional[str],
    #
    # ) -> bool:
    #     """验证 CSRF Token"""
    #     # 两个 Token 都必须存在
    #     if not cookie_token or not header_token:
    #         print(1)
    #         return False
    #
    #     # 使用恒定时间比较
    #     if not hmac.compare_digest(cookie_token, header_token):
    #         print(2)
    #         return False
    #
    #     # 验证 Token 格式
    #     parts = cookie_token.split(":")
    #     if len(parts) != 3:
    #         print(3)
    #         return False
    #
    #     token, timestamp_str, signature = parts
    #
    #     # 验证时间戳
    #     try:
    #         timestamp = int(timestamp_str)
    #         current_time = int(time.time())
    #
    #         # 检查是否过期
    #         if current_time - timestamp > self.max_age:
    #             print(4)
    #             return False
    #     except ValueError:
    #         return False
    #
    #     # 验证签名
    #     data = f"{token}:{timestamp}".encode()
    #     expected_signature = hmac.new(self.secret_key, data, sha256).hexdigest()
    #
    #     if not hmac.compare_digest(signature, expected_signature):
    #         print(5)
    #         return False
    #
    #     # 防止重放攻击
    #     if cookie_token in self.used_tokens:
    #         return False
    #
    #     # 标记为已使用
    #     self.used_tokens.add(cookie_token)
    #
    #     # 清理过期的 Token
    #     self._cleanup_used_tokens()
    #
    #     return True

    async def _verify_csrf_token(
            self,
            redis_client:redis.Redis,
            cookie_token: Optional[str],
            header_token: Optional[str],
    ) -> bool:
        """验证 CSRF Token"""
        # 两个 Token 都必须存在
        if not cookie_token or not header_token:
            print(f"[CSRF验证失败] 原因1: Token缺失 - cookie: {cookie_token}, header: {header_token}")
            return False

        # 使用恒定时间比较
        if not hmac.compare_digest(cookie_token, header_token):
            print(f"[CSRF验证失败] 原因2: Token不匹配")
            print(f"  Cookie token: {cookie_token[:50]}...")
            print(f"  Header token: {header_token[:50]}...")
            return False

        # 验证 Token 格式
        parts = cookie_token.split(":")
        if len(parts) != 3:
            print(f"[CSRF验证失败] 原因3: Token格式错误 - 部分数: {len(parts)}")
            return False

        token, timestamp_str, signature = parts

        # # 验证时间戳
        # try:
        #     timestamp = int(timestamp_str)
        #     current_time = int(time.time())
        #
        #     # 检查是否过期
        #     if current_time - timestamp > self.max_age:
        #         print(f"[CSRF验证失败] 原因4: Token过期")
        #         print(f"  生成时间: {timestamp} ({time.ctime(timestamp)})")
        #         print(f"  当前时间: {current_time} ({time.ctime(current_time)})")
        #         print(f"  时间差: {current_time - timestamp}秒, 最大允许: {self.max_age}秒")
        #         return False
        # except ValueError:
        #     print(f"[CSRF验证失败] 原因5: 时间戳格式错误 - {timestamp_str}")
        #     return False

        # 验证签名
        data = f"{token}:{timestamp_str}".encode()
        expected_signature = hmac.new(self.secret_key, data, sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            print(f"[CSRF验证失败] 原因6: 签名验证失败")
            print(f"  预期签名: {expected_signature}")
            print(f"  实际签名: {signature}")
            return False

        # 防止重放攻击
        #Lua 脚本检查并删除token
        print("开始删除使用后的token")
        key = f"csrf:{cookie_token}"
        print(key)


        script = """
            if redis.call('exists', KEYS[1]) == 1 then
                redis.call('del', KEYS[1])
                return 1
            else
                return 0
            end
            """

        result = await redis_client.eval(script, 1, key)
        if result!=1:
            return False
        # if cookie_token in self.used_tokens:
        #     print(f"[CSRF验证失败] 原因7: Token已使用 - used_tokens集合大小: {len(self.used_tokens)}")
        #     return False
        #
        # # 标记为已使用
        # await self.client.delete(cookie_token)
        # # self.used_tokens.add(cookie_token)
        #
        # print(f"[CSRF验证成功] Token验证通过，已添加到used_tokens")
        #
        # # # 清理过期的 Token
        # # self._cleanup_used_tokens()
        #过期token会自动清除

        return True
    def _cleanup_used_tokens(self):
        """清理过期的已使用 Token"""
        # current_time = int(time.time())
        #
        # # 找出过期的 Token
        # expired = set()
        # for token in self.used_tokens:
        #     parts = token.split(":")
        #     if len(parts) == 3:
        #         try:
        #             timestamp = int(parts[1])
        #             if current_time - timestamp > self.max_age:
        #                 expired.add(token)
        #         except ValueError:
        #             expired.add(token)
        #
        # # 移除过期的 Token
        # self.used_tokens -= expired

    async def store_csrf_token(self, client:redis.Redis, token: str) -> bool:
        """存储 CSRF Token，如果不存在则存储"""
        key = f"csrf:{token}"

        # SET key value NX EX seconds
        result = await client.set(name=key, value="1", nx=True, ex=3600)
        print('将csrf token 存储到redis', result)
        # 返回 True 表示成功存储（之前不存在）
        return result is True

    async def _set_csrf_cookie(self,client:redis.Redis, response: Response, request: Request):
        """设置 CSRF Cookie"""
        # 生成新的 Token
        token = await self._generate_csrf_token()
        result=await self.store_csrf_token(client,token)

        if not result:
            return False

        # 设置 Cookie
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=False,  # 允许前端读取
            secure=request.url.scheme == "https",
            samesite="strict",
            # max_age=self.max_age,
            path="/"
        )
        return True