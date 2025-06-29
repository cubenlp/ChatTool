import httpx
import asyncio
import logging
import time
from chattool.core.config import Config, OpenAIConfig
from chattool.custom_logger import setup_logger
from typing import Generator, AsyncGenerator, Union, Dict, Any, Optional, List
import json

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
    def __init__(self, config:Optional[OpenAIConfig] = None, logger = None, **kwargs):
        if config is None:
            config = OpenAIConfig()
        super().__init__(config, logger, **kwargs)
        
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
        """
        OpenAI Chat Completion API (同步版本)
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: top_p 参数
            max_tokens: 最大token数
            stream: 是否使用流式响应
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False: 返回完整的响应字典
            如果 stream=True: 返回 Generator，yield StreamResponse 对象
        """
        data = {
            "model": model or self.config.model,
            "messages": messages,
            **kwargs
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        if top_p is not None:
            data["top_p"] = top_p 
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        if stream:
            data["stream"] = True
            return self._stream_chat_completion(data)
        
        response = self.post("/chat/completions", data=data)
        return response.json()
    
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
        """
        OpenAI Chat Completion API (异步版本)
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: top_p 参数
            max_tokens: 最大token数
            stream: 是否使用流式响应
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False: 返回完整的响应字典
            如果 stream=True: 返回 AsyncGenerator，async yield StreamResponse 对象
        """
        data = {
            "model": model or self.config.model,
            "messages": messages,
            **kwargs
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        if top_p is not None:
            data["top_p"] = top_p
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        if stream:
            data["stream"] = True
            return self._async_stream_chat_completion(data)
        
        response = await self.async_post("/chat/completions", data=data)
        return response.json()
    
    def _stream_chat_completion(self, data: Dict[str, Any]) -> Generator[StreamResponse, None, None]:
        """同步流式聊天完成 - 返回生成器"""
        client = self._get_sync_client()
        
        with client.stream(
            "POST",
            "/chat/completions",
            json=data,
            headers=self.config.headers
        ) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                # 处理 SSE 格式的数据
                line_str = line.decode('utf-8').strip()
                
                # 跳过非数据行
                if not line_str.startswith('data: '):
                    continue
                
                # 提取数据部分
                data_str = line_str[6:].strip()  # 去掉 'data: ' 前缀
                
                # 检查是否结束
                if data_str == '[DONE]':
                    break
                
                # 跳过空行
                if not data_str:
                    continue
                
                try:
                    # 解析 JSON
                    chunk_data = json.loads(data_str)
                    stream_response = self._process_stream_chunk(chunk_data)
                    yield stream_response
                    
                    # 如果完成，退出循环
                    if stream_response.is_finished:
                        break
                        
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to decode JSON: {e}, data: {data_str}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing stream chunk: {e}")
                    break
    
    async def _async_stream_chat_completion(self, data: Dict[str, Any]) -> AsyncGenerator[StreamResponse, None]:
        """异步流式聊天完成 - 返回异步生成器"""
        client = self._get_async_client()
        
        async with client.stream(
            "POST",
            "/chat/completions",
            json=data,
            headers=self.config.headers
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                # 处理 SSE 格式的数据
                line_str = line.decode('utf-8').strip()
                
                # 跳过非数据行
                if not line_str.startswith('data: '):
                    continue
                
                # 提取数据部分
                data_str = line_str[6:].strip()  # 去掉 'data: ' 前缀
                
                # 检查是否结束
                if data_str == '[DONE]':
                    break
                
                # 跳过空行
                if not data_str:
                    continue
                
                try:
                    # 解析 JSON
                    chunk_data = json.loads(data_str)
                    stream_response = self._process_stream_chunk(chunk_data)
                    yield stream_response
                    
                    # 如果完成，退出循环
                    if stream_response.is_finished:
                        break
                        
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to decode JSON: {e}, data: {data_str}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing stream chunk: {e}")
                    break
    
    def embeddings(
        self, 
        input_text: Union[str, List[str]], 
        model: str = "text-embedding-ada-002", 
        **kwargs
    ) -> Dict[str, Any]:
        """OpenAI Embeddings API"""
        data = {
            "model": model,
            "input": input_text,
            **kwargs
        }
        
        response = self.post("/embeddings", data=data)
        return response.json()
    
    async def async_embeddings(
        self, 
        input_text: Union[str, List[str]], 
        model: str = "text-embedding-ada-002", 
        **kwargs
    ) -> Dict[str, Any]:
        """异步 OpenAI Embeddings API"""
        data = {
            "model": model,
            "input": input_text,
            **kwargs
        }
        
        response = await self.async_post("/embeddings", data=data)
        return response.json()
    
    def _process_stream_chunk(self, chunk_data: Dict[str, Any]) -> StreamResponse:
        """处理流式响应的单个数据块，返回 StreamResponse 对象"""
        return StreamResponse(chunk_data)