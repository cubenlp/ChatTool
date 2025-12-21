import httpx
import json
import os
import logging
import hashlib
from filelock import FileLock
import tempfile
from typing import Awaitable, Callable, List, Dict, Union, Optional, AsyncGenerator, Any
from batch_executor import batch_executor, batch_async_executor, batch_hybrid_executor
from pathlib import Path

from chattool.core.response import ChatResponse
from chattool.utils import valid_models, setup_logger, curl_cmd_of_chat_completion
from chattool.const import (
    OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_API_MODEL,
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_MODEL, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT
)
from .request import HTTPClient

class Chat(HTTPClient):
    def __init__(self, 
        messages: Optional[Union[str, List[Dict[str, str]]]]=None,
        logger: logging.Logger=None,
        api_key: str=None,
        api_base: str=None,
        model: str=None,
        timeout: float = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]]=None,
        **kwargs):
        """初始化聊天模型
        
        Args:
            logger: 日志记录器
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            headers: 自定义 HTTP 头
            **kwargs: 其他配置参数，传入给 data 部分
        """
        logger = logger or setup_logger('Chat')
        if api_key is None:
            api_key = OPENAI_API_KEY
        if model is None:
            model = OPENAI_API_MODEL
        if api_base is None:
            api_base = OPENAI_API_BASE
        if headers is None:
            headers = {
                'Content-Type': 'application/json'
            }
        if not headers.get('Authorization') and api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        super().__init__(
            logger=logger,
            api_base=api_base,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            headers=headers,
            **kwargs
        )
        
        self.api_key = api_key
        self.model = model
        
        # 初始化对话历史
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        self._chat_log: List[Dict] = messages or []
        self._last_response: Optional[ChatResponse] = None
    
    def _prepare_data(self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs) -> Dict[str, Any]:
        """准备请求数据"""
        # 合并参数
        model = model if model is not None else self.model
        data = {
            'model': model, 
            "messages": messages,
            **kwargs
        }
        if temperature is not None:
            data['temperature'] = temperature
        if top_p is not None:
            data['top_p'] = top_p
        if max_tokens is not None:
            data['max_tokens'] = max_tokens
        for k in self.config.kwargs: # 默认的额外参数
            if k not in data and self.config.get(k) is not None:
                data[k] = self.config.get(k)
        return data
    
    def _get_params(self) -> Optional[Dict[str, str]]:
        """合并默认查询参数和自定义参数"""
        return None

    def _get_uri(self)->str:
        """获取请求 URI"""
        return '/chat/completions'
    
    def chat_completion(
        self,
        # data 部分
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs # 其他参数，传入给 data 部分
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
            **kwargs: 其他参数
        """
        # 合并参数
        data = self._prepare_data(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            **kwargs
        )
        if stream:
            # NOTE: 流式响应请使用 chat_completion_stream_async
            pass
        response = self.post(self._get_uri(), data=data, params=self._get_params())
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
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """OpenAI Chat Completion API (异步版本)"""
        # 合并参数
        data = self._prepare_data(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            **kwargs
        )
        if stream:
            # NOTE: 流式响应请使用 chat_completion_stream_async
            pass
        response = await self.async_post(self._get_uri(), data=data, params=self._get_params())
        return response.json()
    
    async def chat_completion_stream_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ):
        """OpenAI Chat Completion API 流式响应（异步版本）"""
        # 合并参数
        data = self._prepare_data(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        # 构建完整 URL
        url = self._build_url(self._get_uri())
        client = self._get_async_client()
        
        async with client.stream(
            method="POST",
            url=url,
            json=data,
            headers=self.config.headers,
            params=self._get_params()
        ) as stream:
            # 检查响应状态码
            if stream.status_code >= 400:
                # 读取错误响应内容
                error_content = await stream.aread()
                try:
                    error_data = json.loads(error_content.decode())
                    error_msg = error_data.get('error', {}).get('message', f'HTTP {stream.status_code}')
                except:
                    error_msg = f'HTTP {stream.status_code}: {error_content.decode()}'
                raise httpx.HTTPStatusError(
                    message=f"API request failed: {error_msg}",
                    request=stream.request,
                    response=stream
                )
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
                    yield response
                    if response.finish_reason == 'stop':
                        break
                except Exception as e:
                    # 其他错误也跳过
                    continue
    
    # === 消息管理 ===
    def add_message(self, role: str, content: str, **kwargs) -> 'Chat':
        """添加消息到对话历史"""
        if role not in ['user', 'assistant', 'system']:
            raise ValueError(f"role 必须是 'user', 'assistant' 或 'system'，收到: {role}")
        
        message = {"role": role, "content": content, **kwargs}
        self._chat_log.append(message)
        return self
    
    def user(self, content: str) -> 'Chat':
        """添加用户消息"""
        return self.add_message('user', content)
    
    def assistant(self, content: str) -> 'Chat':
        """添加助手消息"""
        return self.add_message('assistant', content)
    
    def system(self, content: str) -> 'Chat':
        """添加系统消息"""
        return self.add_message('system', content)
    
    def clear(self) -> 'Chat':
        """清空对话历史"""
        self._chat_log = []
        self._last_response = None
        return self
    
    def pop(self, index: int = -1) -> Dict:
        """移除并返回指定位置的消息"""
        return self._chat_log.pop(index)
    
    # === 核心对话功能 - 子类实现 ===
    def get_response(self, update_history: bool = True, **kwargs) -> ChatResponse:
        """获取对话响应（同步）"""
        response_data = self.chat_completion(
            messages=self._chat_log,
            **kwargs
        )
        response = ChatResponse(response_data)
        self._last_response = response
        if not response.is_valid():
            raise Exception(f"API 返回错误: {response.error_message}")
        if not response.message:
            self.logger.warning("API 返回空消息")
        elif update_history:
            self._chat_log.append(response.message)
        return response
    
    def getresponse(self, update_history: bool = True, **kwargs):
        return self.get_response(update_history, **kwargs)
    
    async def async_get_response(
        self,
        update_history: bool = True,
        **kwargs
    ) -> ChatResponse:
        response_data = await self.async_chat_completion(
            messages=self._chat_log,
            **kwargs
        )
        response = ChatResponse(response_data)
        self._last_response = response
        if not response.is_valid():
            raise Exception(f"API 返回错误: {response.error_message}")
        if not response.message:
            self.logger.warning("API 返回空消息")
        elif update_history:
            self._chat_log.append(response.message)
        return response
    
    async def async_get_response_stream(self, 
            update_history: bool = True,
            stream: bool = True,
            **kwargs
        ) -> AsyncGenerator[ChatResponse, None]:
        """获取流式对话响应（异步）"""
        
        # 用于累积完整的响应内容
        full_content = ""
        last_response = None
        async for response in self.chat_completion_stream_async(
            messages=self._chat_log,
            **kwargs
        ):
            # 保存最后一个响应对象
            last_response = response
            
            # 累积内容
            if response.delta_content:
                full_content += response.delta_content
            
            # 始终yield响应，让调用者决定如何处理
            yield response
        
        # 流式响应结束后，更新历史记录和保存最后响应
        if update_history and full_content:
            self._chat_log.append({
                "role": "assistant",
                "content": full_content
            })
        
        # 构建最终的完整响应对象
        if last_response:
            final_response_data = {
                "id": last_response.id,
                "object": "chat.completion",
                "created": last_response.created,
                "model": last_response.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_content
                    },
                    "finish_reason": "stop"
                }]
            }
            self._last_response = ChatResponse(final_response_data)
        
        # 成功完成，退出重试循环
        return

    def get_valid_models(self, gpt_only: bool = True):
        """获取有效模型列表"""
        # 构建模型URL
        if hasattr(self.config, 'api_base') and self.config.api_base:
            model_url = os.path.join(self.config.api_base, 'models')
        else:
            model_url = "https://api.openai.com/v1/models"
        
        # 获取API密钥
        api_key = getattr(self.config, 'api_key', '') or ''
        
        return valid_models(api_key, model_url, gpt_only=gpt_only)

    # === 便捷方法 ===
    def ask(self, question: str, update_history: bool = True) -> str:
        """问答便捷方法"""
        self.user(question)
        response = self.get_response(update_history=update_history)
        if not update_history:
            self.pop()
        return response.content
    
    async def async_ask(self, question: str, update_history: bool = True) -> str:
        """异步问答便捷方法"""
        self.user(question)
        response = await self.async_get_response(update_history=update_history)
        if not update_history:
            self.pop()
        return response.content
    
    # === 对话历史管理 ===
    def save(self, path: str, mode: str = 'a', index: int = 0):
        """保存对话历史到文件"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        data = {
            "index": index,
            "chat_log": self._chat_log,
        }
        
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    @classmethod
    def load(cls, path: str) -> 'Chat':
        """从文件加载对话历史"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        
        # 使用工厂函数创建正确的实例
        chat = Chat(messages=data['chat_log'])
        return chat
    
    def copy(self) -> 'Chat':
        """复制 Chat 对象"""
        messages = [msg.copy() for msg in self._chat_log]
        return Chat(messages=messages)
    
    @classmethod
    def load_chats(cls, path: Union[str, Path]) -> list[Union['Chat', None]]:
        """从文件加载多个对话历史"""
        path = Path(path)
        if not path.exists():
            return []
        data = path.read_text()
        datas = [json.loads(i) for i in data.splitlines()]
        if not datas:
            return []
        chats = [None] * (max([i['index'] for i in datas]) + 1)
        for data in datas:
            chats[data['index']] = cls(messages=data['chat_log'])
        return chats
    
    # === 显示和调试 ===
    def print_log(self, sep: str = "\n" + "-" * 50 + "\n"):
        """打印对话历史"""
        for msg in self._chat_log:
            role = msg['role'].upper()
            content = msg.get('content', '')
            print(f"{sep}{role}{sep}{content}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            "message_count": len(self._chat_log),
            "model": self.model,
            "api_base": self.config.api_base,
            "last_response": self._last_response.get_debug_info() if self._last_response else None
        }
    
    def print_debug_info(self):
        """打印调试信息"""
        info = self.get_debug_info()
        print("=== Chat Debug Info ===")
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 23)
    
    def print_curl(self, **options):
        """打印等效的 curl 命令"""
        if not self._chat_log:
            print("No messages in chat log to generate curl command.")
            return
        
        # 构建 chat_url
        chat_url = f"{self.config.api_base.rstrip('/')}/chat/completions"
        
        # 生成 curl 命令
        curl_cmd = curl_cmd_of_chat_completion(
            api_key=self.config.api_key,
            chat_url=chat_url,
            messages=self._chat_log,
            model=self.model,
            **options
        )
        print(curl_cmd)
    
    # === 并发执行 ===
    @classmethod
    def batch_process_chat(cls, 
                          messages:list[str],
                          async_func:Callable[[str], Awaitable['Chat']],
                          nworker: int = 1,
                          pool_size:int = 1,
                          checkpoint: Optional[Union[str, Path]] = None,
                          overwrite: bool = False
                          ) -> list['Chat']:
        """批量处理聊天消息
        
        Args:
            messages: 待处理的消息列表
            async_func: 处理函数，输入为消息字符串，输出为处理后的 Chat 对象
        
        Returns:
            处理后的 Chat 对象列表
        """
        chats = [] # 最终结果
        msgs = list(enumerate(messages)) # 处理数据

        # 处理已缓存数据
        if checkpoint is not None: # 缓存存在
            checkpoint = Path(checkpoint)
            # assert checkpoint.suffix in ('.json', '.jsonl'), "Checkpoint file must be JSON or JSONL format"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            if checkpoint.exists():
                if overwrite:
                    checkpoint.unlink()
                else:
                    chats = cls.load_chats(checkpoint)
                    # 跳过已处理数据
                    msgs = [(idt, msg) for idt, msg in enumerate(messages) if idt >= len(chats) or chats[idt] is None]
                    if not msgs:
                        return chats
        # 开始处理数据
        with tempfile.TemporaryDirectory() as temp_dir:
            if checkpoint: # TODO: 多进程模式下使用
                # if pool_id is not None: 
                #     lock = f'{temp_dir}/{checkpoint.stem}_{pool_id}.lock'
                #     dest_file = f'{checkpoint.parent}/{checkpoint.stem}_{pool_id}.{checkpoint.suffix}'
                lock = f'{temp_dir}/{checkpoint}.lock'
            async def process_message(idt_msg:tuple[int, str]) -> Chat:
                idt, msg = idt_msg
                chat = await async_func(msg)
                if checkpoint:
                    with FileLock(lock):
                        chat.save(checkpoint, index=idt)
                return chat
            if pool_size <= 1:
                newchats = batch_async_executor(msgs, process_message, nworker=nworker)
            else:
                newchats = batch_hybrid_executor(msgs, process_message, nworker=nworker, pool_size=pool_size)
        if not chats:
            return newchats
        idt = 0
        for i, chat in enumerate(chats):
            if chat is None:
                chats[i] = newchats[idt]
                idt += 1
        return chats + newchats[idt:]
    
    # === 属性访问 ===
    @property
    def chat_log(self) -> List[Dict]:
        """获取对话历史"""
        return self._chat_log.copy()
    
    @property
    def last_message(self) -> Optional[str]:
        """获取最后一条消息的内容"""
        if self._chat_log:
            return self._chat_log[-1].get('content')
        return None
    
    @property
    def last_response(self) -> Optional[ChatResponse]:
        """获取最后一次响应"""
        return self._last_response
    
    # === 魔术方法 ===
    def __len__(self) -> int:
        return len(self._chat_log)
    
    def __getitem__(self, index) -> Dict:
        return self._chat_log[index]
    
    def __repr__(self) -> str:
        return f"<Chat with {len(self._chat_log)} messages, model: {self.model}>"
    
    def __str__(self) -> str:
        return self.__repr__()

class AzureChat(Chat):
    """Azure OpenAI Chat 实现 - 继承 Chat 复用逻辑"""
    def __init__(self, 
        messages: Optional[Union[str, List[Dict[str, str]]]]=None,
        logger: logging.Logger=None,
        api_key: str=None,
        api_base: str=None,
        api_version: str=None,
        model: str=None,
        timeout: float = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]]=None,
        **kwargs):
        """初始化聊天模型
        
        Args:
            logger: 日志记录器
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            headers: 自定义 HTTP 头
            **kwargs: 其他配置参数，传入给 data 部分
        """
        logger = logger or setup_logger('Chat')
        if api_key is None:
            api_key = AZURE_OPENAI_API_KEY
        if model is None:
            model = AZURE_OPENAI_API_MODEL
        if api_base is None:
            api_base = AZURE_OPENAI_ENDPOINT
        if api_version is None:
            api_version = AZURE_OPENAI_API_VERSION
        if headers is None:
            headers = {
                'Content-Type': 'application/json'
            }
        HTTPClient.__init__(
            self,
            logger=logger,
            api_base=api_base,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            headers=headers,
            **kwargs
        )
        
        self.api_key = api_key
        self.api_version = api_version
        self.model = model
        
        # 初始化对话历史
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        self._chat_log: List[Dict] = messages or []
        self._last_response: Optional[ChatResponse] = None
    
    def _get_params(self) -> Optional[Dict[str, str]]:
        """合并默认查询参数和自定义参数"""
        params = {}
        if self.api_version:
            params['api-version'] = self.api_version
        if self.api_key:
            params['ak'] = self.api_key
        return params
        
    def _get_uri(self) -> str:
        """获取 API URI"""
        return None

    def _generate_log_id(self, messages: List[Dict[str, str]]) -> str:
        """生成请求的 log ID"""
        content = str(messages).encode()
        return hashlib.sha256(content).hexdigest()
