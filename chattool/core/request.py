import httpx
import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Union, Generator, AsyncGenerator, Any
from chattool.core.config import Config, OpenAIConfig, AzureOpenAIConfig
from chattool.custom_logger import setup_logger

# 基础HTTP客户端类
class HTTPClient:
    def __init__(self, config: Optional[Config]=None, logger: Optional[logging.Logger] = None, **kwargs):
        if config is None:
            config = Config()
        for key, value in kwargs.items():
            setattr(config, key, value)
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
    
    def _retry_request(self, request_func, *args, **kwargs):
        """重试机制装饰器"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return request_func(*args, **kwargs)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # 指数退避
                else:
                    self.logger.error(f"Request failed after {self.config.max_retries + 1} attempts")
        
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
                    self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"Request failed after {self.config.max_retries + 1} attempts")
        
        raise last_exception
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """同步请求"""
        client = self._get_sync_client()
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if headers:
            merged_headers.update(headers)
        
        def _make_request():
            return client.request(
                method=method,
                url=endpoint,
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
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """异步请求"""
        client = self._get_async_client()
        
        # 合并headers
        merged_headers = self.config.headers.copy()
        if headers:
            merged_headers.update(headers)
        
        async def _make_request():
            return await client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=merged_headers,
                **kwargs
            )
        response = await self._async_retry_request(_make_request)
        response.raise_for_status()
        return response
    
    # 便捷方法
    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("POST", endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("PUT", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", endpoint, **kwargs)
    
    # 异步便捷方法
    async def async_get(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self.async_request("GET", endpoint, **kwargs)
    
    async def async_post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.async_request("POST", endpoint, data=data, **kwargs)
    
    async def async_put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.async_request("PUT", endpoint, data=data, **kwargs)
    
    async def async_delete(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self.async_request("DELETE", endpoint, **kwargs)
    
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

class StreamResponse:
    """流式响应包装类"""
    
    def __init__(self, chunk_data: Dict[str, Any]):
        self.raw = chunk_data
        self.id = chunk_data.get('id')
        self.object = chunk_data.get('object')
        self.created = chunk_data.get('created')
        self.model = chunk_data.get('model')
        
        choices = chunk_data.get('choices', [])
        if choices:
            choice = choices[0]
            self.delta = choice.get('delta', {})
            self.finish_reason = choice.get('finish_reason')
            self.content = self.delta.get('content', '')
            self.role = self.delta.get('role')
        else:
            self.delta = {}
            self.finish_reason = None
            self.content = ''
            self.role = None
    
    @property
    def has_content(self) -> bool:
        """是否包含内容"""
        return bool(self.content)
    
    @property
    def is_finished(self) -> bool:
        """是否完成"""
        return self.finish_reason == 'stop'
    
    def __str__(self):
        return self.content
    
    def __repr__(self):
        return f"StreamResponse(content='{self.content}', finish_reason='{self.finish_reason}')"

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
        if param_name in kwargs:
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
    ) -> Union[Dict[str, Any], Generator[StreamResponse, None, None]]:
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
            return self._stream_chat_completion(data, uri, request_headers)
        
        response = self.post(uri, data=data, headers=request_headers)
        return response.json()
    
    async def async_chat_completion(
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
    ) -> Union[Dict[str, Any], AsyncGenerator[StreamResponse, None]]:
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
            return self._async_stream_chat_completion(data, uri, request_headers)
        
        response = await self.async_post(uri, data=data, headers=request_headers)
        return response.json()
    
    def _stream_chat_completion(
        self, 
        data: Dict[str, Any], 
        uri: str = '/chat/completions',
        headers: Optional[Dict[str, str]] = None
    ) -> Generator[StreamResponse, None, None]:
        """同步流式聊天完成"""
        client = self._get_sync_client()
        request_headers = headers or self.config.headers
        
        with client.stream(
            "POST",
            uri,
            json=data,
            headers=request_headers
        ) as response:
            response.raise_for_status()
            yield from self._process_stream_response(response.iter_lines())
    
    async def _async_stream_chat_completion(
        self, 
        data: Dict[str, Any], 
        uri: str = '/chat/completions',
        headers: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[StreamResponse, None]:
        """异步流式聊天完成"""
        client = self._get_async_client()
        request_headers = headers or self.config.headers
        
        async with client.stream(
            "POST",
            uri,
            json=data,
            headers=request_headers
        ) as response:
            response.raise_for_status()
            async for chunk in self._async_process_stream_response(response.aiter_lines()):
                yield chunk
    
    def _process_stream_response(self, lines):
        """处理流式响应行"""
        for line in lines:
            if not line:
                continue
            
            line_str = line.decode('utf-8').strip()
            chunk = self._parse_stream_line(line_str)
            if chunk:
                yield chunk
                if chunk.is_finished:
                    break
    
    async def _async_process_stream_response(self, lines):
        """异步处理流式响应行"""
        async for line in lines:
            if not line:
                continue
            
            line_str = line.decode('utf-8').strip()
            chunk = self._parse_stream_line(line_str)
            if chunk:
                yield chunk
                if chunk.is_finished:
                    break
    
    def _parse_stream_line(self, line_str: str) -> Optional[StreamResponse]:
        """解析单行流式响应"""
        if not line_str.startswith('data: '):
            return None
        
        data_str = line_str[6:].strip()
        
        if data_str == '[DONE]':
            return None
        
        if not data_str:
            return None
        
        try:
            chunk_data = json.loads(data_str)
            return self._process_stream_chunk(chunk_data)
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to decode JSON: {e}, data: {data_str}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing stream chunk: {e}")
            return None
    
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
    
    def _process_stream_chunk(self, chunk_data: Dict[str, Any]) -> StreamResponse:
        """处理流式响应的单个数据块"""
        return StreamResponse(chunk_data)
    
    # 通用的简化请求方法
    def simple_request(self, input_text: Union[str, List[Dict[str, str]]], model_name: Optional[str] = None, **kwargs) -> str:
        """简化的请求方法，直接返回内容字符串"""
        if isinstance(input_text, str):
            messages = [{"role": "user", "content": input_text}]
        else:
            messages = input_text
        
        response = self.chat_completion(messages, model=model_name, **kwargs)
        return response['choices'][0]['message']['content']


class AzureOpenAIClient(OpenAIClient):
    """Azure OpenAI 客户端"""
    
    _config_only_attrs = {
        'api_key', 'api_base', 'api_version',
        'headers', 'timeout', 'max_retries', 'retry_delay'
    }
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None, logger = None, **kwargs):
        if config is None:
            config = AzureOpenAIConfig()
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
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Generator[StreamResponse, None, None]]:
        """Azure OpenAI Chat Completion API (同步版本)"""
        # 调用父类方法，但使用空字符串作为 URI（因为 api_base 已经是完整地址）
        return super().chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream,
            uri="",  # Azure 的 api_base 已经是完整地址
            **kwargs
        )
    
    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[StreamResponse, None]]:
        """Azure OpenAI Chat Completion API (异步版本)"""
        # 调用父类方法
        return await super().async_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream,
            uri="",
            **kwargs
        )