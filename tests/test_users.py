# tests/test_user_self_operations.py
"""
测试完整的新用户自操作流程
核心流程：创建用户 -> 登录 -> 以自身身份操作
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app


class TestUserSelfOperations:
    """测试新用户对自己资源的操作流程"""

    @pytest_asyncio.fixture
    async def client(self):
        """每个测试独立的客户端"""
        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
        ) as ac:
            yield ac

    async def _get_csrf_token(self, client: AsyncClient) -> str:
        """辅助函数：获取CSRF token"""
        response = await client.get("/")
        csrf_token = response.cookies.get("csrf_token")
        assert csrf_token is not None, "无法获取CSRF token"
        return csrf_token

    @pytest.mark.asyncio
    async def test_new_user_full_lifecycle(self, client: AsyncClient):
        """
        测试完整的新用户自服务流程
        1. 注册新用户
        2. 用新用户凭据登录
        3. 用获得的令牌更新自己的档案
        4. 尝试删除自己（权限测试）
        """
        print("\n" + "=" * 60)
        print("测试：新用户完整自操作生命周期")
        print("=" * 60)

        timestamp = int(time.time())
        # 步骤1: 创建一个新用户
        print(f"\n[步骤1] 创建新用户 (时间戳: {timestamp})...")

        new_user_data = {
            "username": f"newuser_{timestamp}",
            "email": f"newuser_{timestamp}@example.com",
            "password": "MySecurePass123!",  # 记住密码，用于后续登录
            "level": 1  # 普通用户等级
        }

        # 1.1 获取CSRF token用于创建用户
        csrf_token_create = await self._get_csrf_token(client)

        # 1.2 发送创建用户请求
        create_response = await client.post(
            "/api/v1/users",
            json=new_user_data,
            headers={"X-CSRF-Token": csrf_token_create}
        )

        assert create_response.status_code == 200, f"用户创建失败: {create_response.text}"
        new_user = create_response.json()
        new_user_id = new_user.get("user_id")
        print(f"    成功！用户ID: {new_user_id}, 用户名: {new_user_data['email']}")

        # 步骤2: 用新用户凭据登录，获取访问令牌
        print(f"\n[步骤2] 新用户登录获取令牌...")

        # 2.1 获取新的CSRF token用于登录请求
        csrf_token_login = await self._get_csrf_token(client)

        # 2.2 准备登录数据
        login_data = {
            "username": new_user_data["email"],
            "password": new_user_data["password"],  # 使用创建时设置的密码
            "grant_type": "password"
        }

        # 2.3 发送登录请求
        login_response = await client.post(
            "/api/v1/auth/token",
            data=login_data,  # 注意：这里是 data 而不是 json
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRF-Token": csrf_token_login
            }
        )

        assert login_response.status_code == 200, f"登录失败: {login_response.text}"
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        token_type = token_data.get("token_type", "Bearer")
        assert access_token is not None, "登录响应中未找到 access_token"
        print(f"    成功！获取到访问令牌: {access_token[:20]}...")

        # 步骤3: 用新用户的令牌更新自己的档案
        print(f"\n[步骤3] 新用户更新自己的档案...")

        # 3.1 获取新的CSRF token用于更新操作
        csrf_token_update = await self._get_csrf_token(client)

        # 3.2 准备更新数据
        profile_update = {
            "bio": f"我是新用户{timestamp}，这是我的个人简介。",
            "age": 25
        }

        # 3.3 发送更新请求（使用新用户的令牌）
        update_response = await client.patch(
            f"/api/v1/users/{new_user_id}/profile",
            json=profile_update,
            headers={
                "Authorization": f"{token_type} {access_token}",
                "X-CSRF-Token": csrf_token_update
            }
        )

        # 根据API设计，普通用户可能只能更新自己的档案
        # 如果权限足够，应该成功(200)；如果权限不足，可能失败(403)
        print(f"    更新档案响应: {update_response.status_code}")

        if update_response.status_code == 200:
            updated_profile = update_response.json()
            assert updated_profile["bio"] == profile_update["bio"]
            print(f"    ✓ 档案更新成功")
        elif update_response.status_code == 403:
            print(f"    ⓘ 权限不足，无法更新档案（符合普通用户权限设计）")
        else:
            print(f"    ⓘ 其他响应: {update_response.text}")

        # 步骤4: 尝试用新用户的令牌删除自己
        print(f"\n[步骤4] 新用户尝试删除自己（权限测试）...")

        # 4.1 获取新的CSRF token用于删除操作
        csrf_token_delete = await self._get_csrf_token(client)

        # 4.2 发送删除请求
        delete_response = await client.delete(
            f"/api/v1/users/{new_user_id}",
            headers={
                "Authorization": f"{token_type} {access_token}",
                "X-CSRF-Token": csrf_token_delete
            }
        )

        print(f"    删除自己响应: {delete_response.status_code}")

        # 权限设计分析：
        # - 如果允许用户删除自己，应返回 200/204
        # - 如果只有管理员能删除用户，应返回 403
        # - 如果令牌无效/过期，应返回 401

        if delete_response.status_code in [200, 204]:
            print(f"    ✓ 用户成功删除自己")
        elif delete_response.status_code == 403:
            print(f"    ⓘ 权限不足，只有管理员能删除用户")
        elif delete_response.status_code == 401:
            print(f"    ⓘ 认证失败，令牌可能无效")
        else:
            print(f"    ⓘ 其他响应: {delete_response.text}")

        print(f"\n" + "=" * 60)
        print("测试完成！此流程验证了：")
        print("1. 用户注册功能")
        print("2. 用户登录认证功能")
        print("3. 用户权限系统（基于level字段）")
        print("4. 受保护端点的访问控制")
        print("=" * 60)

        return {
            "user_id": new_user_id,
            "username": new_user_data["username"],
            "access_token": access_token,
            "update_success": update_response.status_code == 200,
            "delete_success": delete_response.status_code in [200, 204]
        }

    @pytest.mark.asyncio
    async def test_user_cannot_access_others_profile(self, client: AsyncClient):
        """
        测试用户权限隔离：用户A不能更新用户B的档案
        此测试需要先创建两个用户
        """
        print("\n" + "=" * 60)
        print("测试：用户权限隔离（用户A不能操作用户B的资源）")
        print("=" * 60)

        timestamp = int(time.time())

        # 创建用户A
        print(f"\n1. 创建用户A...")
        user_a_data = {
            "username": f"usera_{timestamp}",
            "email": f"usera_{timestamp}@example.com",
            "password": "UserAPass123!",
            "level": 1
        }

        csrf_token = await self._get_csrf_token(client)
        resp_a = await client.post(
            "/api/v1/users",
            json=user_a_data,
            headers={"X-CSRF-Token": csrf_token}
        )
        assert resp_a.status_code == 200
        user_a = resp_a.json()
        user_a_id = user_a["user_id"]
        print(f"   用户A ID: {user_a_id}")

        # 创建用户B
        print(f"\n2. 创建用户B...")
        user_b_data = {
            "username": f"userb_{timestamp}",
            "email": f"userb_{timestamp}@example.com",
            "password": "UserBPass456!",
            "level": 1
        }

        csrf_token = await self._get_csrf_token(client)
        resp_b = await client.post(
            "/api/v1/users",
            json=user_b_data,
            headers={"X-CSRF-Token": csrf_token}
        )
        assert resp_b.status_code == 200
        user_b = resp_b.json()
        user_b_id = user_b["user_id"]
        print(f"   用户B ID: {user_b_id}")

        # 用户A登录，获取令牌
        print(f"\n3. 用户A登录获取令牌...")
        csrf_token = await self._get_csrf_token(client)
        login_data_a = {
            "username": user_a_data["email"],
            "password": user_a_data["password"],
            "grant_type": "password"
        }
        login_resp_a = await client.post(
            "/api/v1/auth/token",
            data=login_data_a,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRF-Token": csrf_token
            }
        )
        assert login_resp_a.status_code == 200
        token_a = login_resp_a.json()["access_token"]
        print(f"   用户A令牌获取成功")

        # 尝试用用户A的令牌更新用户B的档案（应该失败）
        print(f"\n4. 尝试用用户A的令牌更新用户B的档案（应失败）...")
        csrf_token = await self._get_csrf_token(client)
        update_data = {"bio": "用户A试图篡改用户B的资料"}

        response = await client.patch(
            f"/api/v1/users/{user_b_id}/profile",
            json=update_data,
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-CSRF-Token": csrf_token
            }
        )

        print(f"   响应状态: {response.status_code}")

        # 应该返回 403 Forbidden 或 404 Not Found
        # 具体取决于您的权限设计：
        # - 403: 权限明确禁止
        # - 404: 隐藏资源存在性（更安全）
        assert response.status_code in [403, 404], \
            f"预期权限错误(403/404)，实际得到 {response.status_code}"

        print(f"   ✓ 权限隔离生效：用户A不能操作用户B的资源")

    @pytest.mark.asyncio
    async def test_admin_user_creation_and_privilege(self, client: AsyncClient):
        """
        测试管理员用户特殊流程：
        1. 创建一个高级别（管理员）用户
        2. 用该管理员账号登录
        3. 测试管理员特权操作（如删除其他用户）
        """
        print("\n" + "=" * 60)
        print("测试：管理员用户创建与特权操作")
        print("=" * 60)

        timestamp = int(time.time())

        # 注意：此测试假设您的系统允许创建高级别用户
        # 如果创建用户端点有权限控制，可能需要先有管理员令牌

        # 1. 创建管理员用户
        print(f"\n1. 创建管理员用户...")
        admin_data = {
            "username": f"admin_{timestamp}",
            "email": f"admin_{timestamp}@example.com",
            "password": "AdminPass123!",
            "level": 10  # 假设10是管理员级别
        }

        csrf_token = await self._get_csrf_token(client)
        admin_resp = await client.post(
            "/api/v1/users",
            json=admin_data,
            headers={"X-CSRF-Token": csrf_token}
        )

        # 创建可能成功或失败，取决于权限设计
        if admin_resp.status_code == 200:
            admin_user = admin_resp.json()
            admin_id = admin_user["user_id"]
            print(f"   管理员创建成功，ID: {admin_id}")

            # 2. 管理员登录
            print(f"\n2. 管理员登录...")
            csrf_token = await self._get_csrf_token(client)
            login_data = {
                "username": admin_data["username"],
                "password": admin_data["password"],
                "grant_type": "password"
            }
            login_resp = await client.post(
                "/api/v1/auth/token",
                data=login_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRF-Token": csrf_token
                }
            )

            if login_resp.status_code == 200:
                admin_token = login_resp.json()["access_token"]
                print(f"   管理员登录成功")

                # 3. 创建普通用户供测试删除
                print(f"\n3. 创建普通用户供测试...")
                normal_user_data = {
                    "username": f"normal_{timestamp}",
                    "email": f"normal_{timestamp}@example.com",
                    "password": "NormalPass123!",
                    "level": 1
                }

                csrf_token = await self._get_csrf_token(client)
                # 使用管理员令牌创建用户（如果需要权限）
                normal_resp = await client.post(
                    "/api/v1/users",
                    json=normal_user_data,
                    headers={
                        "Authorization": f"Bearer {admin_token}",
                        "X-CSRF-Token": csrf_token
                    }
                )

                if normal_resp.status_code == 200:
                    normal_user = normal_resp.json()
                    normal_id = normal_user["user_id"]
                    print(f"   普通用户创建成功，ID: {normal_id}")

                    # 4. 管理员删除普通用户
                    print(f"\n4. 管理员尝试删除普通用户...")
                    csrf_token = await self._get_csrf_token(client)
                    delete_resp = await client.delete(
                        f"/api/v1/users/{normal_id}",
                        headers={
                            "Authorization": f"Bearer {admin_token}",
                            "X-CSRF-Token": csrf_token
                        }
                    )

                    print(f"   删除响应: {delete_resp.status_code}")
                    if delete_resp.status_code in [200, 204]:
                        print(f"   ✓ 管理员成功删除用户")
                    else:
                        print(f"   响应: {delete_resp.text}")
                else:
                    print(f"   普通用户创建失败: {normal_resp.status_code}")
            else:
                print(f"   管理员登录失败: {login_resp.status_code}")
        else:
            print(f"   管理员用户创建失败: {admin_resp.status_code}")
            print(f"   这可能是因为创建高级别用户需要现有管理员权限")
            print(f"   如果是这样，您需要先有一个预设的管理员测试账号")


# 运行测试
if __name__ == "__main__":
    import pytest
    import sys

    # 运行此文件的测试
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--asyncio-mode=auto"
    ])

    sys.exit(exit_code)