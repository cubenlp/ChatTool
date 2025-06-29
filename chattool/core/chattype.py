from typing import List, Dict, Union, Optional, Generator, AsyncGenerator, Any
import json
import os
import time
import random
import asyncio
from loguru import logger
from chattool.core.config import OpenAIConfig
from chattool.core.request import OpenAIClient, StreamResponse
from chattool.core.response import ChatResponse


class Chat(OpenAIClient):
    """简化的 Chat 类 - 专注于基础对话功能"""
    
    def __init__(
        self,
        msg: Union[List[Dict], str, None] = None,
        config: Optional[OpenAIConfig] = None,
        **kwargs
    ):
        """
        初始化 Chat 对象
        
        Args:
            msg: 初始消息，可以是字符串、消息列表或 None
            config: OpenAI 配置对象
            **kwargs: 其他配置参数（会覆盖 config 中的设置）
        """
        # 初始化配置
        if config is None:
            config = OpenAIConfig()
        
        # 应用 kwargs 覆盖配置
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        super().__init__(config)
        
        # 初始化对话历史
        self._chat_log = self._init_messages(msg)
        self._last_response: Optional[ChatResponse] = None
    
    def _init_messages(self, msg: Union[List[Dict], str, None]) -> List[Dict]:
        """初始化消息列表"""
        if msg is None:
            return []
        elif isinstance(msg, str):
            return [{"role": "user", "content": msg}]
        elif isinstance(msg, list):
            # 验证消息格式
            for m in msg:
                if not isinstance(m, dict) or 'role' not in m:
                    raise ValueError("消息列表中的每个元素都必须是包含 'role' 键的字典")
            return msg.copy()
        else:
            raise ValueError("msg 必须是字符串、字典列表或 None")
    
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
    
    # === 核心对话功能 ===
    def get_response(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """
        获取对话响应（同步）
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            update_history: 是否更新对话历史
            **options: 传递给 chat_completion 的其他参数
        """
        # 合并配置
        chat_options = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # 调用 OpenAI API
                response_data = self.chat_completion(
                    messages=self._chat_log,
                    **chat_options
                )
                
                # 包装响应
                response = ChatResponse(response_data)
                
                # 验证响应
                if not response.is_valid():
                    raise Exception(f"API 返回错误: {response.error_message}")
                
                # 更新历史记录
                if update_history and response.message:
                    self._chat_log.append(response.message)
                
                self._last_response = response
                return response
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                else:
                    self.logger.error(f"请求在 {max_retries + 1} 次尝试后失败")
        
        raise last_error
    
    async def async_get_response(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """
        获取对话响应（异步）
        """
        chat_options = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response_data = await self.async_chat_completion(
                    messages=self._chat_log,
                    **chat_options
                )
                
                response = ChatResponse(response_data)
                
                if not response.is_valid():
                    raise Exception(f"API 返回错误: {response.error_message}")
                
                if update_history and response.message:
                    self._chat_log.append(response.message)
                
                self._last_response = response
                return response
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"请求在 {max_retries + 1} 次尝试后失败")
        
        raise last_error
    
    # === 流式响应 ===
    def stream_response(self, **options) -> Generator[str, None, None]:
        """
        流式获取响应内容（同步）
        返回生成器，逐个 yield 内容片段
        """
        chat_options = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            **options
        }
        
        full_content = ""
        
        try:
            for stream_resp in self.chat_completion(
                messages=self._chat_log,
                stream=True,
                **chat_options
            ):
                if stream_resp.has_content:
                    content = stream_resp.content
                    full_content += content
                    yield content
                
                if stream_resp.is_finished:
                    break
            
            # 更新历史记录
            if full_content:
                self._chat_log.append({
                    "role": "assistant",
                    "content": full_content
                })
                
        except Exception as e:
            self.logger.error(f"流式响应失败: {e}")
            raise
    
    async def async_stream_response(self, **options) -> AsyncGenerator[str, None]:
        """
        流式获取响应内容（异步）
        """
        chat_options = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            **options
        }
        
        full_content = ""
        
        try:
            async for stream_resp in self.async_chat_completion(
                messages=self._chat_log,
                stream=True,
                **chat_options
            ):
                if stream_resp.has_content:
                    content = stream_resp.content
                    full_content += content
                    yield content
                
                if stream_resp.is_finished:
                    break
            
            # 更新历史记录
            if full_content:
                self._chat_log.append({
                    "role": "assistant", 
                    "content": full_content
                })
                
        except Exception as e:
            self.logger.error(f"异步流式响应失败: {e}")
            raise
    
    # === 便捷方法 ===
    def ask(self, question: str, **options) -> str:
        """
        问答便捷方法
        
        Args:
            question: 问题
            **options: 传递给 get_response 的参数
            
        Returns:
            回答内容
        """
        self.user(question)
        response = self.get_response(**options)
        return response.content
    
    async def async_ask(self, question: str, **options) -> str:
        """异步问答便捷方法"""
        self.user(question)
        response = await self.async_get_response(**options)
        return response.content
    
    # === 对话历史管理 ===
    def save(self, path: str, mode: str = 'a', index: int = 0):
        """保存对话历史到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        data = {
            "index": index,
            "chat_log": self._chat_log,
            "config": {
                "model": self.config.model,
                "api_base": self.config.api_base
            }
        }
        
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    @classmethod
    def load(cls, path: str) -> 'Chat':
        """从文件加载对话历史"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        
        chat = cls(msg=data['chat_log'])
        
        # 如果有配置信息，应用它们
        if 'config' in data:
            for key, value in data['config'].items():
                if hasattr(chat.config, key):
                    setattr(chat.config, key, value)
        
        return chat
    
    def copy(self) -> 'Chat':
        """复制 Chat 对象"""
        return Chat(msg=self._chat_log.copy(), config=self.config)
    
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
            "model": self.config.model,
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
        return f"<Chat with {len(self._chat_log)} messages, model: {self.config.model}>"
    
    def __str__(self) -> str:
        return self.__repr__()