import pytest
from fastapi.testclient import TestClient
from app.main import app  # 请替换为您的实际应用导入路径

# 创建测试客户端
client = TestClient(app)


def get_csrf_token():
    """辅助函数：获取新的CSRF token"""
    csrf_response = client.get("/")
    assert csrf_response.status_code == 200

    # 尝试从cookie获取
    csrf_token = csrf_response.cookies.get("csrf_token")

    # 如果不在cookie中，可能在响应体中
    if csrf_token is None:
        csrf_data = csrf_response.json()
        csrf_token = csrf_data.get("csrf_token")

    assert csrf_token is not None, "Failed to get CSRF token from GET response"
    return csrf_token


def test_create_user_success_with_fresh_csrf():
    """
    测试使用新鲜的CSRF token创建用户成功
    每个POST请求都需要新的CSRF token
    """
    # 步骤1: 获取新的CSRF token
    csrf_token = get_csrf_token()

    # 步骤2: 使用新鲜的CSRF token创建用户
    user_data = {
        "username": "fresh_user_1",
        "email": "fresh1@example.com",
        "password": "SecurePass123!",
        "level": 1
    }

    create_response = client.post(
        "/api/v1/users",
        json=user_data,
        headers={
            "X-CSRF-Token": csrf_token
        }
    )

    # 验证创建成功
    assert create_response.status_code == 200, f"User creation failed: {create_response.text}"

    # 验证响应体结构
    response_data = create_response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]

    return response_data


def test_csrf_token_single_use():
    """
    测试CSRF token只能使用一次
    使用过的token再次使用应该失败
    """
    # 第一次：获取token并成功使用
    csrf_token = get_csrf_token()

    user_data_1 = {
        "username": "single_use_user_1",
        "email": "single1@example.com",
        "password": "password123",
        "level": 1
    }

    response1 = client.post(
        "/api/v1/users",
        json=user_data_1,
        headers={
            "X-CSRF-Token": csrf_token
        }
    )

    # 第一次请求应该成功
    assert response1.status_code == 200, "First request with fresh token should succeed"

    # 第二次：尝试使用同一个token（应该失败）
    user_data_2 = {
        "username": "single_use_user_2",
        "email": "single2@example.com",
        "password": "password456",
        "level": 2
    }

    response2 = client.post(
        "/api/v1/users",
        json=user_data_2,
        headers={
            "X-CSRF-Token": csrf_token  # 使用已经用过的token
        }
    )

    # 第二次请求应该失败（token已使用）
    assert response2.status_code in [401, 403], \
        f"Second request with used token should fail, got {response2.status_code}"

    # 第三次：获取新token并成功使用
    new_csrf_token = get_csrf_token()

    user_data_3 = {
        "username": "single_use_user_3",
        "email": "single3@example.com",
        "password": "password789",
        "level": 3
    }

    response3 = client.post(
        "/api/v1/users",
        json=user_data_3,
        headers={
            "X-CSRF-Token": new_csrf_token  # 使用新token
        }
    )

    # 使用新token的请求应该成功
    assert response3.status_code == 200, "Request with new token should succeed"


def test_create_user_missing_csrf_token():
    """
    测试缺少CSRF token时创建用户失败
    """
    # 不需要先获取token，直接发送没有token的请求
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "missing_token_user",
            "email": "missing@example.com",
            "password": "password123",
            "level": 1
        }
        # 故意不设置X-CSRF-Token头
    )

    # 应该返回403或401
    assert create_response.status_code in [401, 403], \
        f"Expected 401 or 403 for missing CSRF token, got {create_response.status_code}"


def test_create_user_wrong_csrf_token():
    """
    测试使用错误的CSRF token时创建用户失败
    """
    # 获取正确的CSRF token（但不使用）
    csrf_token = get_csrf_token()

    # 使用错误的token
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "wrong_token_user",
            "email": "wrong@example.com",
            "password": "password123",
            "level": 1
        },
        headers={
            "X-CSRF-Token": "wrong_token_here"  # 错误的token
        }
    )

    # 应该返回403或401
    assert create_response.status_code in [401, 403], \
        f"Expected 401 or 403 for wrong CSRF token, got {create_response.status_code}"

    # 注意：即使请求失败，这个错误的token也被认为是"使用过"的
    # 但正确的token仍然有效，可以用于下一次请求
    user_data = {
        "username": "correct_token_user",
        "email": "correct@example.com",
        "password": "password456",
        "level": 2
    }

    response_with_correct = client.post(
        "/api/v1/users",
        json=user_data,
        headers={
            "X-CSRF-Token": csrf_token  # 使用之前获取的正确token
        }
    )

    # 正确的token应该仍然有效
    assert response_with_correct.status_code == 200, "Correct token should still work after wrong token attempt"


def test_create_user_invalid_data_with_fresh_token():
    """
    测试使用无效数据创建用户（每次都需要新token）
    """
    # 测试1: 缺少必填字段
    csrf_token1 = get_csrf_token()

    invalid_data_missing = {
        "username": "incomplete_user",
        # 缺少email, password, level
    }

    response1 = client.post(
        "/api/v1/users",
        json=invalid_data_missing,
        headers={
            "X-CSRF-Token": csrf_token1
        }
    )

    # 应该返回422验证错误
    assert response1.status_code == 422

    # 测试2: 无效的邮箱格式（需要新token）
    csrf_token2 = get_csrf_token()

    invalid_data_email = {
        "username": "bademailuser",
        "email": "not-an-email",  # 无效的邮箱格式
        "password": "password123",
        "level": 1
    }

    response2 = client.post(
        "/api/v1/users",
        json=invalid_data_email,
        headers={
            "X-CSRF-Token": csrf_token2
        }
    )

    # 根据您的验证逻辑，这可能返回422或其他状态码
    assert response2.status_code in [422, 400]

    # 测试3: 无效的level值（需要新token）
    csrf_token3 = get_csrf_token()

    invalid_data_level = {
        "username": "badleveluser",
        "email": "badlevel@example.com",
        "password": "password123",
        "level": "not_an_integer"  # 应该是整数
    }

    response3 = client.post(
        "/api/v1/users",
        json=invalid_data_level,
        headers={
            "X-CSRF-Token": csrf_token3
        }
    )

    assert response3.status_code == 422


def test_create_duplicate_user_with_fresh_tokens():
    """
    测试创建重复用户名的用户（每次都需要新token）
    """
    # 第一次创建用户
    csrf_token1 = get_csrf_token()

    user_data = {
        "username": "duplicate_test_user",
        "email": "duplicate1@example.com",
        "password": "password123",
        "level": 1
    }

    first_response = client.post(
        "/api/v1/users",
        json=user_data,
        headers={
            "X-CSRF-Token": csrf_token1
        }
    )

    # 如果第一次创建成功
    if first_response.status_code == 200:
        # 尝试用相同的用户名再次创建（需要新token）
        csrf_token2 = get_csrf_token()

        duplicate_data = {
            "username": "duplicate_test_user",  # 相同的用户名
            "email": "duplicate2@example.com",  # 不同的邮箱
            "password": "password456",
            "level": 2
        }

        second_response = client.post(
            "/api/v1/users",
            json=duplicate_data,
            headers={
                "X-CSRF-Token": csrf_token2
            }
        )

        # 应该返回冲突错误（409）或其他错误状态码
        assert second_response.status_code in [409, 400, 422], \
            f"Expected conflict for duplicate username, got {second_response.status_code}"


def test_multiple_successful_requests_with_fresh_tokens():
    """
    测试多个成功请求，每个都需要新token
    """
    users_created = []

    # 创建3个用户，每个都需要新token
    for i in range(3):
        csrf_token = get_csrf_token()

        user_data = {
            "username": f"multi_user_{i}",
            "email": f"multi{i}@example.com",
            "password": f"Password{i}123!",
            "level": i + 1
        }

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={
                "X-CSRF-Token": csrf_token
            }
        )

        # 每个请求都应该成功
        assert response.status_code == 200, f"Request {i} failed: {response.text}"

        response_data = response.json()
        assert response_data["username"] == user_data["username"]
        users_created.append(response_data)

    # 验证创建了3个用户
    assert len(users_created) == 3
    print(f"Successfully created {len(users_created)} users with fresh CSRF tokens")


def test_csrf_token_expires_after_failed_request():
    """
    测试即使请求失败，CSRF token也会失效
    """
    # 获取token
    csrf_token = get_csrf_token()

    # 第一次请求：使用无效数据（应该失败）
    invalid_data = {
        "username": "",  # 空的用户名
        "email": "invalid@example.com",
        "password": "password123",
        "level": 1
    }

    response1 = client.post(
        "/api/v1/users",
        json=invalid_data,
        headers={
            "X-CSRF-Token": csrf_token
        }
    )

    # 请求应该因为数据无效而失败
    assert response1.status_code in [422, 400], \
        f"Expected validation error, got {response1.status_code}"

    # 第二次请求：尝试使用同一个token（应该失败，因为token已使用）
    valid_data = {
        "username": "after_failure_user",
        "email": "after@example.com",
        "password": "password456",
        "level": 2
    }

    response2 = client.post(
        "/api/v1/users",
        json=valid_data,
        headers={
            "X-CSRF-Token": csrf_token  # 使用已经用过的token
        }
    )

    # 应该失败，因为token已使用
    assert response2.status_code in [401, 403], \
        f"Token should be invalid after failed request, got {response2.status_code}"

    # 第三次请求：获取新token并成功
    new_csrf_token = get_csrf_token()

    response3 = client.post(
        "/api/v1/users",
        json=valid_data,
        headers={
            "X-CSRF-Token": new_csrf_token  # 使用新token
        }
    )

    # 使用新token应该成功
    assert response3.status_code == 200, "New token should work after failed request"


def test_get_users_list_no_csrf_required():
    """
    测试获取用户列表（GET请求不需要CSRF token）
    可以多次调用而不需要新token
    """
    # 第一次GET请求
    response1 = client.get("/api/v1/users")
    assert response1.status_code == 200

    # 第二次GET请求（不需要新token）
    response2 = client.get("/api/v1/users")
    assert response2.status_code == 200

    # 第三次GET请求（不需要新token）
    response3 = client.get("/api/v1/users")
    assert response3.status_code == 200

    # 验证响应结构
    users_list = response3.json()
    assert isinstance(users_list, list)

    print(f"GET requests don't require CSRF tokens. Retrieved {len(users_list)} users")


# 使用pytest夹具（每次测试获取新token）
@pytest.fixture
def fresh_csrf_token():
    """为每个测试提供新鲜的CSRF token"""
    return get_csrf_token()


def test_create_user_with_fixture(fresh_csrf_token):
    """
    使用夹具测试创建用户
    夹具确保每次测试都有新鲜的CSRF token
    """
    user_data = {
        "username": "fixture_fresh_user",
        "email": "fixture_fresh@example.com",
        "password": "FixturePass123!",
        "level": 1
    }

    response = client.post(
        "/api/v1/users",
        json=user_data,
        headers={
            "X-CSRF-Token": fresh_csrf_token
        }
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]


def test_concurrent_csrf_token_usage():
    """
    测试并发场景下的CSRF token使用
    每个token只能用于一个请求
    """
    # 获取多个token
    tokens = [get_csrf_token() for _ in range(3)]

    results = []

    # 同时使用这些token（在实际并发中，这些请求可能几乎同时发生）
    for i, token in enumerate(tokens):
        user_data = {
            "username": f"concurrent_user_{i}",
            "email": f"concurrent{i}@example.com",
            "password": f"Concurrent{i}123!",
            "level": i + 1
        }

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={
                "X-CSRF-Token": token
            }
        )

        results.append({
            "token_index": i,
            "status_code": response.status_code,
            "success": response.status_code == 200
        })

    # 统计成功次数
    success_count = sum(1 for r in results if r["success"])
    print(f"Concurrent test: {success_count} out of {len(results)} requests succeeded")

    # 所有使用不同token的请求都应该成功
    # 因为每个token都是新鲜的且只使用一次
    assert success_count == len(results), \
        f"All fresh tokens should work. Results: {results}"


if __name__ == "__main__":
    # 直接运行测试（用于调试）
    import sys

    pytest.main(sys.argv)