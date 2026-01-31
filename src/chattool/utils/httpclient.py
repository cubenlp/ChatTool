import httpx
import asyncio
import logging
import time
from typing import Dict, Optional, Any
from chattool.utils import setup_logger

class HTTPConfig:
    def __init__(
        self,
        api_base: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ):
        self.api_base = api_base
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.kwargs = kwargs
    
    def get(self, key, default=None):
        return getattr(self, key, self.kwargs.get(key, default))
    
    def copy(self):
        return HTTPConfig(
            api_base=self.api_base,
            headers=self.headers.copy(),
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            **self.kwargs
        )
    
    def create(self, **kwargs):
        config = self.copy()
        config.kwargs.update(kwargs)
        return config
    
    def __repr__(self):
        text = f"{self.__class__.__name__}("
        if self.api_base:
            text += f"api_base={self.api_base}, "
        text += f"timeout={self.timeout}, max_retries={self.max_retries}, retry_delay={self.retry_delay})"
        return text

# 基础HTTP客户端类
class HTTPClient:
    def __init__(
         self, 
         logger: Optional[logging.Logger] = None, 
         api_base: str = "",
         headers: Optional[Dict[str, str]] = None,
         timeout: float = 0,
         max_retries: int = 3,
         retry_delay: float = 1.0,
         **kwargs):
        self.config = HTTPConfig(
            api_base=api_base,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs
        )
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
        self.logger = logger or setup_logger(self.__class__.__name__)
    
    def _get_sync_client(self) -> httpx.Client:
        """获取同步客户端，懒加载"""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.api_base,
                headers=self.config.headers,
                timeout=self.config.timeout if self.config.timeout > 0 else None
            )
        return self._sync_client
    
    def _get_async_client(self) -> httpx.AsyncClient:
        """获取异步客户端，懒加载"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.api_base,
                headers=self.config.headers,
                timeout=self.config.timeout if self.config.timeout > 0 else None
            )
        return self._async_client
    
    def _build_url(self, url: str) -> str:
        """构建完整的请求 URL"""
        if not url:
            # 如果 url 为空，直接使用 api_base
            return self.config.api_base
        
        # 如果 url 已经是完整 URL，直接返回
        if url.startswith(('http://', 'https://')):
            return url
            
        # 处理相对路径
        base = self.config.api_base.rstrip('/')
        url = url.lstrip('/')
        
        if url:
            return f"{base}/{url}"
        else:
            return base
    
    def _retry_request(self, request_func, *args, **kwargs):
        """重试机制装饰器"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return request_func(*args, **kwargs)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.config.max_retries + 1}): {e}")
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # 指数退避
                else:
                    self.logger.error(f"请求失败，已尝试 {self.config.max_retries + 1} 次")
        
        raise last_exception
    
    async def _async_retry_request(self, request_func, *args, **kwargs):
        """异步重试机制"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await request_func(*args, **kwargs)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.config.max_retries + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"请求失败，已尝试 {self.config.max_retries + 1} 次")
        
        raise last_exception
    
    def request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """同步请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE, etc.)
            url: 请求URL，相对路径或完整URL
            data: 请求体数据，JSON格式
            params: 查询参数
            headers: 自定义请求头
        """
        client = self._get_sync_client()
        
        # 构建完整 URL
        url = self._build_url(url)
        
        if headers is None:
            headers = self.config.headers
        def _make_request():
            return client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                **kwargs
            )
        
        response = self._retry_request(_make_request)
        response.raise_for_status()
        return response
    
    async def async_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """异步请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE, etc.)
            url: 请求URL，相对路径或完整URL
            data: 请求体数据，JSON格式
            params: 查询参数
            headers: 自定义请求头
        """
        client = self._get_async_client()
        
        # 构建完整 URL
        url = self._build_url(url)
        if headers is None:
            headers = self.config.headers
        
        async def _make_request():
            return await client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                **kwargs
            )
        response: httpx.Response = await self._async_retry_request(_make_request)
        response.raise_for_status()
        return response
    
    # 便捷方法
    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("POST", url, data=data, **kwargs)
    
    def put(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("PUT", url, data=data, **kwargs)
    
    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)
    
    # 异步便捷方法
    async def async_get(self, url: str, **kwargs) -> httpx.Response:
        return await self.async_request("GET", url, **kwargs)
    
    async def async_post(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.async_request("POST", url, data=data, **kwargs)
    
    async def async_put(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.async_request("PUT", url, data=data, **kwargs)
    
    async def async_delete(self, url: str, **kwargs) -> httpx.Response:
        return await self.async_request("DELETE", url, **kwargs)
    
    def close(self):
        """关闭客户端连接"""
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            asyncio.create_task(self._async_client.aclose())
    
    async def aclose(self):
        """异步关闭客户端连接"""
        if self._async_client:
            await self._async_client.aclose()
        if self._sync_client:
            self._sync_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
