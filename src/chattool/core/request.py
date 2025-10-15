import httpx
import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Union, Generator, AsyncGenerator, Any
from chattool.core.config import Config, OpenAIConfig, AzureOpenAIConfig
from chattool.core.response import ChatResponse
from batch_executor import setup_logger

# 基础HTTP客户端类
class HTTPClient:
    def __init__(self, config: Optional[Config]=None, logger: Optional[logging.Logger] = None, **kwargs):
        if config is None:
            config = Config()
        config.update_kwargs(**kwargs)
        self.config = config
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
        if logger is None:
            self.logger = setup_logger(self.__class__.__name__)
        else:
            self.logger = logger
    
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
        """同步请求"""
        client = self._get_sync_client()
        
        # 构建完整 URL
        url = self._build_url(url)
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if headers:
            merged_headers.update(headers)
        
        def _make_request():
            return client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=merged_headers,
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
        """异步请求"""
        client = self._get_async_client()
        
        # 构建完整 URL
        url = self._build_url(url)
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if headers:
            merged_headers.update(headers)
        
        async def _make_request():
            return await client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=merged_headers,
                **kwargs
            )
        response = await self._async_retry_request(_make_request)
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

class OpenAIClient(HTTPClient):
    _config_only_attrs = {
        'api_key', 'api_base', 'headers', 'timeout', 
        'max_retries', 'retry_delay'
    }
    
    def __init__(self, config: Optional[OpenAIConfig] = None, logger = None, **kwargs):
        if config is None:
            config = OpenAIConfig()
        super().__init__(config, logger, **kwargs)
    
    def _build_chat_data(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """构建聊天完成请求的数据"""
        data = {"messages": messages}
        
        # 处理所有可能的参数
        all_params = set(kwargs.keys()) | {
            k for k in self.config.__dict__.keys() 
            if not k.startswith('_')  # 排除私有属性
        }
        
        for param_name in all_params:
            # 跳过配置专用属性
            if param_name in self._config_only_attrs:
                continue
                
            value = self._get_param_value(param_name, kwargs)
            if value is not None:
                data[param_name] = value
                
        return data
    
    def _get_param_value(self, param_name: str, kwargs: Dict[str, Any]):
        """按优先级获取参数值：kwargs > config > None"""
        if kwargs.get(param_name) is not None:
            return kwargs[param_name]
        return self.config.get(param_name)
    
    def _prepare_headers(self, messages: List[Dict[str, str]], custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """准备请求头 - 子类可以重写此方法"""
        headers = self.config.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        uri: str = '/chat/completions',
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI Chat Completion API (同步版本)
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: top_p 参数
            max_tokens: 最大token数
            stream: 是否使用流式响应
            uri: 请求 URI
            headers: 自定义请求头
            **kwargs: 其他参数
        """
        # 合并参数
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': stream,
            **kwargs
        }
        
        # 构建数据和请求头
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages, headers)
        
        if data.get('stream'):
            data['stream'] = False #TODO: 流式响应不支持
        
        response = self.post(uri, data=data, headers=request_headers)
        return response.json()
    
    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        uri: str = '/chat/completions',
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """OpenAI Chat Completion API (异步版本)"""
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': stream,
            **kwargs
        }
        
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages, headers)
        
        if data.get('stream'):
            return self.chat_completion_stream_async(
                messages=messages,
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                uri=uri,
                headers=headers,
                **kwargs
            )
        
        response = await self.async_post(uri, data=data, headers=request_headers)
        return response.json()
    
    async def chat_completion_stream_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        uri: str = '/chat/completions',
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """OpenAI Chat Completion API 流式响应（异步版本）"""
        # 合并参数
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': True,
            **kwargs
        }
        # 构建数据和请求头
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages, headers)
        
        # 构建完整 URL
        url = self._build_url(uri)
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if request_headers:
            merged_headers.update(request_headers)
        
        client = self._get_async_client()
        
        async with client.stream(
            method="POST",
            url=url,
            json=data,
            headers=merged_headers
        ) as stream:
            async for line in stream.aiter_lines():
                if not line:
                    continue
                # 去掉 "data: " 前缀
                if line.startswith("data: "):
                    line = line[6:]
                
                # 检查是否结束
                if line.strip() == "[DONE]":
                    break
                
                # 跳过空行
                if not line.strip():
                    continue
                
                try:
                    # 解析 JSON
                    chunk_data = json.loads(line)
                    response = ChatResponse(chunk_data)
                    
                    # 跳过空的 choices 数组
                    if not response.choices:
                        continue
                    
                    # yield 所有有效的响应
                    yield response
                    
                    # 检查是否完成
                    if response.finish_reason == 'stop':
                        break
                        
                except json.JSONDecodeError as e:
                    # 跳过无法解析的行
                    continue
                except Exception as e:
                    # 其他错误也跳过
                    continue

    def embeddings(
        self, 
        input_text: Union[str, List[str]], 
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """OpenAI Embeddings API"""
        all_kwargs = {
            'model': model or self.config.get('model', 'text-embedding-ada-002'),
            'input': input_text,
            **kwargs
        }
        
        data = {}
        for key, value in all_kwargs.items():
            if value is not None:
                data[key] = value
        
        response = self.post("/embeddings", data=data)
        return response.json()
    
    async def async_embeddings(
        self, 
        input_text: Union[str, List[str]], 
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步 OpenAI Embeddings API"""
        all_kwargs = {
            'model': model or self.config.get('model', 'text-embedding-ada-002'),
            'input': input_text,
            **kwargs
        }
        
        data = {}
        for key, value in all_kwargs.items():
            if value is not None:
                data[key] = value
        
        response = await self.async_post("/embeddings", data=data)
        return response.json()

class AzureOpenAIClient(OpenAIClient):
    """Azure OpenAI 客户端"""
    
    _config_only_attrs = {
        'api_key', 'api_base', 'api_version',
        'headers', 'timeout', 'max_retries', 'retry_delay'
    }
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None, logger = None, **kwargs):
        if config is None:
            config = AzureOpenAIConfig()
        self.config = config
        super().__init__(config, logger, **kwargs)
    
    def _generate_log_id(self, messages: List[Dict[str, str]]) -> str:
        """生成请求的 log ID"""
        content = str(messages).encode()
        return hashlib.sha256(content).hexdigest()
    
    def _prepare_headers(self, messages: List[Dict[str, str]], custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """准备 Azure 专用请求头"""
        headers = self.config.headers.copy()
        headers['X-TT-LOGID'] = self._generate_log_id(messages)
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _prepare_params(self, custom_params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """准备 Azure API 请求参数"""
        params = self.config.get_request_params()
        if custom_params:
            params.update(custom_params)
        return params
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        uri: str = '',
        params: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Azure OpenAI Chat Completion API (同步版本)"""
        
        # 合并参数
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': stream,
            **kwargs
        }
        
        # 构建数据和请求头
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages)
        request_params = self._prepare_params(params)
        
        if data.get('stream'):
            data['stream'] = False #TODO: 流式响应不支持
        
        response = self.post(uri, data=data, headers=request_headers, params=request_params)
        return response.json()
    
    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        uri: str = '',
        params: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """Azure OpenAI Chat Completion API (异步版本)"""
        
        # 合并参数
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': stream,
            **kwargs
        }
        
        # 构建数据和请求头
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages)
        request_params = self._prepare_params(params)
        
        if data.get('stream'):
            return self.chat_completion_stream_async(
                messages=messages,
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                uri=uri,
                params=params,
                **kwargs
            )
        
        response = await self.async_post(uri, data=data, headers=request_headers, params=request_params)
        return response.json()
    
    async def chat_completion_stream_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        uri: str = '',
        params: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Azure OpenAI Chat Completion API 流式响应（异步版本）"""
        # 合并参数
        all_kwargs = {
            'model': model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': True,
            **kwargs
        }
        
        # 构建数据和请求头
        data = self._build_chat_data(messages, **all_kwargs)
        request_headers = self._prepare_headers(messages)
        request_params = self._prepare_params(params)
        
        # 构建完整 URL
        url = self._build_url(uri)
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if request_headers:
            merged_headers.update(request_headers)
        
        client = self._get_async_client()
        
        async with client.stream(
            method="POST",
            url=url,
            json=data,
            headers=merged_headers,
            params=request_params
        ) as stream:
            async for line in stream.aiter_lines():
                if not line:
                    continue
                
                # 去掉 "data: " 前缀
                if line.startswith("data: "):
                    line = line[6:]
                
                # 检查是否结束
                if line.strip() == "[DONE]":
                    break
                
                # 跳过空行
                if not line.strip():
                    continue
                
                try:
                    # 解析 JSON
                    chunk_data = json.loads(line)
                    response = ChatResponse(chunk_data)
                    
                    # 检查是否有内容
                    if response.delta and 'content' in response.delta:
                        yield response
                    
                    # 检查是否完成
                    if response.finish_reason == 'stop':
                        break
                        
                except json.JSONDecodeError as e:
                    # 跳过无法解析的行
                    continue
                except Exception as e:
                    # 其他错误也跳过
                    continue
    
    async def async_embeddings(
        self, 
        input_text: Union[str, List[str]], 
        model: Optional[str] = None,
        uri: str = '',
        params: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步 Azure OpenAI Embeddings API"""
        all_kwargs = {
            'model': model or self.config.get('model', 'text-embedding-ada-002'),
            'input': input_text,
            **kwargs
        }
        
        data = {}
        for key, value in all_kwargs.items():
            if value is not None:
                data[key] = value
        
        request_params = self._prepare_params(params)
        response = await self.async_post(uri, data=data, params=request_params)
        return response.json()
