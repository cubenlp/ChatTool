import asyncio
import pytest
from chattool.core import HTTPClient, Config
from httpx import Response

class TestHTTPClient:
    """HTTPClient 测试类"""
    
    def test_client_initialization(self, config):
        """测试客户端初始化"""
        client = HTTPClient(config)
        assert client.config.api_base == 'http://127.0.0.1:8000'
        assert client.logger is not None
        assert client._sync_client is None
        assert client._async_client is None
    
    # def test_client_with_kwargs(self, config):
    #     """测试使用 kwargs 初始化"""
    #     client = HTTPClient(config, timeout=30, custom_param="test")
    #     assert hasattr(client.config, 'timeout')
    #     assert hasattr(client.config, 'custom_param')
    #     assert client.config.custom_param == "test"
    
    def test_get_request(self, http_client):
        """测试 GET 请求"""
        response = http_client.get("/test-get")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["request_info"]["method"] == "GET"
        assert data["request_info"]["path"] == "test-get"
    
    def test_post_request(self, http_client):
        """测试 POST 请求"""
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
        
        # 验证请求体
        import json
        body_data = json.loads(data["request_info"]["body"])
        assert body_data == test_data
    
    def test_put_request(self, http_client):
        """测试 PUT 请求"""
        test_data = {"update": "value"}
        
        response = http_client.put("/test-put", data=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_info"]["method"] == "PUT"
    
    def test_delete_request(self, http_client):
        """测试 DELETE 请求"""
        response = http_client.delete("/test-delete")
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_info"]["method"] == "DELETE"
    
    def test_request_with_params(self, http_client):
        """测试带查询参数的请求"""
        params = {
            "page": 1,
            "size": 10,
            "filter": "active"
        }
        
        response = http_client.get("/test-params", params=params)
        assert response.status_code == 200
        
        data = response.json()
        query_params = data["request_info"]["query_params"]
        assert query_params["page"] == "1"  # URL参数都是字符串
        assert query_params["size"] == "10"
        assert query_params["filter"] == "active"
    
    def test_request_with_headers(self, http_client):
        """测试带自定义请求头的请求"""
        custom_headers = {
            "X-Custom-Header": "test-value",
            "X-Request-ID": "12345"
        }
        
        response = http_client.get("/test-headers", headers=custom_headers)
        assert response.status_code == 200
        
        data = response.json()
        headers = data["request_info"]["headers"]
        assert headers["x-custom-header"] == "test-value"  # FastAPI 转换为小写
        assert headers["x-request-id"] == "12345"
    
    def test_nested_path(self, http_client):
        """测试嵌套路径"""
        response = http_client.get("/api/v1/users/123/profile")
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_info"]["path"] == "api/v1/users/123/profile"
    
    def test_root_path(self, http_client):
        """测试根路径"""
        response = http_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_info"]["path"] == ""
    
    def test_context_manager(self, config):
        """测试上下文管理器"""
        with HTTPClient(config) as client:
            response = client.get("/test-context")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_get_request(self, http_client):
        """测试异步 GET 请求"""
        response = await http_client.async_get("/test-async-get")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["request_info"]["method"] == "GET"
    
    @pytest.mark.asyncio
    async def test_async_post_request(self, http_client):
        """测试异步 POST 请求"""
        test_data = {"async": "test", "timestamp": "2024-01-01"}
        
        response = await http_client.async_post("/test-async-post", data=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_info"]["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, config):
        """测试异步上下文管理器"""
        async with HTTPClient(config) as client:
            response = await client.async_get("/test-async-context")
            assert response.status_code == 200
    
    def test_request_info_structure(self, http_client):
        """测试返回的请求信息结构"""
        response = http_client.get("/test-structure")
        data = response.json()
        
        # 验证基本结构
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
        
        # 验证客户端信息结构
        client_info = request_info["client"]
        assert "host" in client_info
        assert "port" in client_info
    
    def test_large_payload(self, http_client):
        """测试大载荷"""
        large_data = {
            "items": [{"id": i, "name": f"item_{i}"} for i in range(100)],
            "description": "A" * 1000  # 1000字符的字符串
        }
        
        response = http_client.post("/test-large-payload", data=large_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
    
    def test_special_characters(self, http_client):
        """测试特殊字符"""
        test_data = {
            "chinese": "你好世界",
            "emoji": "🚀🎉",
            "special": "!@#$%^&*()",
            "unicode": "\u2603"  # 雪人符号
        }
        
        response = http_client.post("/test-special-chars", data=test_data)
        assert response.status_code == 200


# 参数化测试
class TestHTTPClientParametrized:
    """参数化测试"""
    
    @pytest.mark.parametrize("method,endpoint", [
        ("GET", "/param-test-get"),
        ("POST", "/param-test-post"),
        ("PUT", "/param-test-put"),
        ("DELETE", "/param-test-delete"),
    ])
    def test_http_methods(self, http_client, method, endpoint):
        """参数化测试不同的HTTP方法"""
        if method == "GET":
            response = http_client.get(endpoint)
        elif method == "POST":
            response = http_client.post(endpoint, data={"test": "data"})
        elif method == "PUT":
            response = http_client.put(endpoint, data={"test": "data"})
        elif method == "DELETE":
            response = http_client.delete(endpoint)
        
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
    def test_various_paths(self, http_client, path):
        """测试各种路径格式"""
        response = http_client.get(path)
        assert response.status_code == 200
        
        data = response.json()
        expected_path = path[1:]  # 去掉开头的 "/"
        assert data["request_info"]["path"] == expected_path


# 性能测试
class TestHTTPClientPerformance:
    """性能测试"""
    
    def test_multiple_requests(self, http_client):
        """测试多个连续请求"""
        for i in range(10):
            response = http_client.get(f"/perf-test/{i}")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, http_client):
        """测试并发请求"""
        tasks = []
        for i in range(5):
            task = http_client.async_get(f"/concurrent-test/{i}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            assert response.status_code == 200
