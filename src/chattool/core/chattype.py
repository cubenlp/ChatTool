from typing import List, Dict, Union, Optional, Generator, AsyncGenerator, Any
import json
import os
import time
import asyncio
import logging
from batch_executor import setup_logger
from chattool.core.config import Config, OpenAIConfig, AzureOpenAIConfig
from chattool.core.request import OpenAIClient, AzureOpenAIClient
from chattool.core.response import ChatResponse


def Chat(
    config: Optional[Union[OpenAIConfig, AzureOpenAIConfig]] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Union['ChatOpenAI', 'ChatAzure']:
    """
    Chat 工厂函数 - 根据配置类型自动选择正确的客户端
    
    Args:
        config: 配置对象（OpenAIConfig 或 AzureOpenAIConfig）
        logger: 日志实例
        **kwargs: 其他配置参数
        
    Returns:
        ChatOpenAI 或 ChatAzure 实例
    """
    if config is None:
        config = OpenAIConfig()
    
    logger = logger or setup_logger('Chat')
    
    if isinstance(config, AzureOpenAIConfig):
        return ChatAzure(config=config, logger=logger, **kwargs)
    elif isinstance(config, OpenAIConfig):
        return ChatOpenAI(config=config, logger=logger, **kwargs)
    else:
        raise ValueError(f"不支持的配置类型: {type(config)}")


class ChatBase:
    """Chat 基类 - 定义对话管理功能"""
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None, **kwargs):
        self.config = config
        self.logger = logger or setup_logger('ChatBase')
        
        # 初始化对话历史
        self._chat_log: List[Dict] = []
        self._last_response: Optional[ChatResponse] = None
    
    # === 消息管理 ===
    def add_message(self, role: str, content: str, **kwargs) -> 'ChatBase':
        """添加消息到对话历史"""
        if role not in ['user', 'assistant', 'system']:
            raise ValueError(f"role 必须是 'user', 'assistant' 或 'system'，收到: {role}")
        
        message = {"role": role, "content": content, **kwargs}
        self._chat_log.append(message)
        return self
    
    def user(self, content: str) -> 'ChatBase':
        """添加用户消息"""
        return self.add_message('user', content)
    
    def assistant(self, content: str) -> 'ChatBase':
        """添加助手消息"""
        return self.add_message('assistant', content)
    
    def system(self, content: str) -> 'ChatBase':
        """添加系统消息"""
        return self.add_message('system', content)
    
    def clear(self) -> 'ChatBase':
        """清空对话历史"""
        self._chat_log = []
        self._last_response = None
        return self
    
    def pop(self, index: int = -1) -> Dict:
        """移除并返回指定位置的消息"""
        return self._chat_log.pop(index)
    
    # === 核心对话功能 - 子类实现 ===
    def get_response(self, **options) -> ChatResponse:
        raise NotImplementedError("子类必须实现 get_response 方法")
    
    async def get_response_async(self, **options) -> ChatResponse:
        raise NotImplementedError("子类必须实现 get_response_async 方法")

    async def get_response_stream_async(self, **options) -> AsyncGenerator[ChatResponse, None]:
        raise NotImplementedError("子类必须实现 get_response_stream 方法")
    
    # === 便捷方法 ===
    def ask(self, question: str, **options) -> str:
        """问答便捷方法"""
        self.user(question)
        response = self.get_response(**options)
        return response.content
    
    async def ask_async(self, question: str, **options) -> str:
        """异步问答便捷方法"""
        self.user(question)
        response = await self.get_response_async(**options)
        return response.content
    
    # === 对话历史管理 ===
    def save(self, path: str, mode: str = 'a', index: int = 0):
        """保存对话历史到文件"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        data = {
            "index": index,
            "chat_log": self._chat_log,
            "config_type": type(self.config).__name__,
            "config": {
                "model": self.config.model,
                "api_base": self.config.api_base
            }
        }
        
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    @classmethod
    def load(cls, path: str) -> 'ChatBase':
        """从文件加载对话历史"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        
        # 根据保存的配置类型创建相应的配置对象
        config_type = data.get('config_type', 'OpenAIConfig')
        if config_type == 'AzureOpenAIConfig':
            config = AzureOpenAIConfig()
        else:
            config = OpenAIConfig()
        
        # 应用保存的配置
        if 'config' in data:
            for key, value in data['config'].items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # 使用工厂函数创建正确的实例
        chat = Chat(config=config)
        chat._chat_log = data['chat_log']
        return chat
    
    def copy(self) -> 'ChatBase':
        """复制 Chat 对象"""
        new_chat = Chat(config=self.config)
        new_chat._chat_log = self._chat_log.copy()
        return new_chat
    
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
            "config_type": type(self.config).__name__,
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
        config_type = type(self.config).__name__
        return f"<Chat({config_type}) with {len(self._chat_log)} messages, model: {self.config.model}>"
    
    def __str__(self) -> str:
        return self.__repr__()


class ChatOpenAI(ChatBase, OpenAIClient):
    """OpenAI Chat 实现"""
    
    def __init__(self, config=None, logger=None, **kwargs):
        # 先初始化 OpenAIClient（底层 HTTP 客户端）
        OpenAIClient.__init__(self, config, logger, **kwargs)
        # 再初始化 ChatBase（对话管理功能）
        ChatBase.__init__(self, config, logger, **kwargs)
    
    def get_response(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """获取对话响应（同步）"""
        chat_options = {
            "model": self.config.model,
            "temperature": getattr(self.config, 'temperature', None),
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response_data = self.chat_completion(
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
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"请求在 {max_retries + 1} 次尝试后失败")
        
        raise last_error
    
    async def get_response_stream_async(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> AsyncGenerator[ChatResponse, None]:
        """获取流式对话响应（异步）"""
        chat_options = {
            "model": self.config.model,
            "temperature": getattr(self.config, 'temperature', None),
            "stream": True,
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # 用于累积完整的响应内容
                full_content = ""
                last_response = None
                
                async for response in self.chat_completion_stream_async(
                    messages=self._chat_log,
                    **chat_options
                ):
                    # 保存最后一个响应对象
                    last_response = response
                    
                    # 累积内容
                    if response.delta_content:
                        full_content += response.delta_content
                    
                    # 始终yield响应，让调用者决定如何处理
                    yield response
                    
                    # 检查是否完成
                    if response.finish_reason == 'stop':
                        break
                
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
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    self.logger.warning(f"流式请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"流式请求在 {max_retries + 1} 次尝试后失败")
        
        # 如果所有重试都失败了，抛出最后一个错误
        if last_error:
            raise last_error
        raise last_error
    
    async def get_response_async(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """获取对话响应（异步）"""
        chat_options = {
            "model": self.config.model,
            "temperature": getattr(self.config, 'temperature', None),
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response_data = await self.chat_completion_async(
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
    


class ChatAzure(ChatBase, AzureOpenAIClient):
    """Azure OpenAI Chat 实现 - 继承 ChatOpenAI 复用逻辑"""
    
    def __init__(self, config=None, logger=None, **kwargs):
        # 替换为 AzureOpenAIClient 初始化
        AzureOpenAIClient.__init__(self, config, logger, **kwargs)
        ChatBase.__init__(self, config, logger, **kwargs)
    
    def get_response(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """获取对话响应（同步）"""
        chat_options = {
            "model": self.config.model,
            "temperature": getattr(self.config, 'temperature', None),
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response_data = self.chat_completion(
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
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"请求在 {max_retries + 1} 次尝试后失败")
        
        raise last_error
    
    async def get_response_async(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        update_history: bool = True,
        **options
    ) -> ChatResponse:
        """获取对话响应（异步）"""
        chat_options = {
            "model": self.config.model,
            "temperature": getattr(self.config, 'temperature', None),
            **options
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response_data = await self.chat_completion_async(
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
