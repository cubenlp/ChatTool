import json
import asyncio
import pytest
from chattool.utils import HTTPClient

# 初始化与配置相关测试
def test_client_initialization(config):
    client = HTTPClient(api_base=config.api_base)
    assert client.config.api_base == 'http://127.0.0.1:8000'
    assert client.logger is not None
    assert client._sync_client is None
    assert client._async_client is None


def test_client_with_kwargs(config):
    client = HTTPClient(api_base=config.api_base, timeout=30, custom_param="test")
    assert hasattr(client.config, 'timeout')
    assert client.config.get("custom_param") == "test"


# 同步请求测试
def test_get_request(http_client: HTTPClient):
    response = http_client.get("/test-get")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["request_info"]["method"] == "GET"
    assert data["request_info"]["path"] == "test-get"


def test_post_request(http_client: HTTPClient):
    test_data = {
        "name": "test",
        "value": 123,
        "items": ["a", "b", "c"]
    }

    response = http_client.post("/test-post", data=test_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["request_info"]["method"] == "POST"
    assert data["request_info"]["path"] == "test-post"

    
    body_data = json.loads(data["request_info"]["body"])
    assert body_data == test_data


def test_put_request(http_client: HTTPClient):
    test_data = {"update": "value"}

    response = http_client.put("/test-put", data=test_data)
    assert response.status_code == 200

    data = response.json()
    assert data["request_info"]["method"] == "PUT"


def test_delete_request(http_client: HTTPClient):
    response = http_client.delete("/test-delete")
    assert response.status_code == 200

    data = response.json()
    assert data["request_info"]["method"] == "DELETE"


def test_request_with_params(http_client: HTTPClient):
    params = {
        "page": 1,
        "size": 10,
        "filter": "active"
    }

    response = http_client.get("/test-params", params=params)
    assert response.status_code == 200

    data = response.json()
    query_params = data["request_info"]["query_params"]
    assert query_params["page"] == "1"
    assert query_params["size"] == "10"
    assert query_params["filter"] == "active"


def test_request_with_headers(http_client: HTTPClient):
    custom_headers = {
        "X-Custom-Header": "test-value",
        "X-Request-ID": "12345"
    }

    response = http_client.get("/test-headers", headers=custom_headers)
    assert response.status_code == 200

    data = response.json()
    headers = data["request_info"]["headers"]
    assert headers["x-custom-header"] == "test-value"
    assert headers["x-request-id"] == "12345"


def test_nested_path(http_client: HTTPClient):
    response = http_client.get("/api/v1/users/123/profile")
    assert response.status_code == 200

    data = response.json()
    assert data["request_info"]["path"] == "api/v1/users/123/profile"


def test_root_path(http_client: HTTPClient):
    response = http_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["request_info"]["path"] == ""


def test_context_manager(config):
    with HTTPClient(api_base=config.api_base) as client:
        response = client.get("/test-context")
        assert response.status_code == 200


# 异步请求测试
@pytest.mark.asyncio
async def test_async_get_request(http_client: HTTPClient):
    response = await http_client.async_get("/test-async-get")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["request_info"]["method"] == "GET"


@pytest.mark.asyncio
async def test_async_post_request(http_client: HTTPClient):
    test_data = {"async": "test", "timestamp": "2024-01-01"}

    response = await http_client.async_post("/test-async-post", data=test_data)
    assert response.status_code == 200

    data = response.json()
    assert data["request_info"]["method"] == "POST"


@pytest.mark.asyncio
async def test_concurrent_requests_isolated_client(config):
    async with HTTPClient(api_base=config.api_base) as client:
        tasks = [client.async_get(f"/concurrent-test/{i}") for i in range(5)]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


@pytest.mark.asyncio
async def test_async_context_manager(config):
    async with HTTPClient(api_base=config.api_base) as client:
        response = await client.async_get("/test-async-context")
        assert response.status_code == 200


def test_request_info_structure(http_client: HTTPClient):
    response = http_client.get("/test-structure")
    data = response.json()

    assert "status" in data
    assert "message" in data
    assert "request_info" in data

    request_info = data["request_info"]
    required_fields = [
        "timestamp", "method", "url", "path",
        "client", "headers", "query_params", "body"
    ]

    for field in required_fields:
        assert field in request_info

    client_info = request_info["client"]
    assert "host" in client_info
    assert "port" in client_info


def test_large_payload(http_client: HTTPClient):
    large_data = {
        "items": [{"id": i, "name": f"item_{i}"} for i in range(100)],
        "description": "A" * 1000
    }

    response = http_client.post("/test-large-payload", data=large_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"


def test_special_characters(http_client: HTTPClient):
    test_data = {
        "chinese": "你好世界",
        "emoji": "🚀🎉",
        "special": "!@#$%^&*()",
        "unicode": "\u2603"
    }

    response = http_client.post("/test-special-chars", data=test_data)
    assert response.status_code == 200


# 参数化测试
@pytest.mark.parametrize("method,url", [
    ("GET", "/param-test-get"),
    ("POST", "/param-test-post"),
    ("PUT", "/param-test-put"),
    ("DELETE", "/param-test-delete"),
])
def test_http_methods(http_client: HTTPClient, method, url):
    if method == "GET":
        response = http_client.get(url)
    elif method == "POST":
        response = http_client.post(url, data={"test": "data"})
    elif method == "PUT":
        response = http_client.put(url, data={"test": "data"})
    elif method == "DELETE":
        response = http_client.delete(url)
    else:
        raise AssertionError("Unsupported method")

    assert response.status_code == 200
    data = response.json()
    assert data["request_info"]["method"] == method


@pytest.mark.parametrize("path", [
    "/simple",
    "/api/v1/test",
    "/very/deep/nested/path/test",
    "/path-with-dashes",
    "/path_with_underscores",
    "/123/numeric/456",
])
def test_various_paths(http_client: HTTPClient, path):
    response = http_client.get(path)
    assert response.status_code == 200

    data = response.json()
    expected_path = path[1:]
    assert data["request_info"]["path"] == expected_path


# 性能相关测试
def test_multiple_requests(http_client: HTTPClient):
    for i in range(10):
        response = http_client.get(f"/perf-test/{i}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_requests_with_fixture(http_client: HTTPClient):
    tasks = [http_client.async_get(f"/concurrent-test/{i}") for i in range(5)]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 200