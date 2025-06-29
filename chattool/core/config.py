from typing import Dict, Optional
from chattool.utils import get_secure_api_key
import os

# 基础配置类 - 最通用的 HTTP 交互
class Config:
    def __init__(
        self,
        api_key: str = "",
        api_base: str = "",
        model: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"api_key={get_secure_api_key(self.api_key)}, "
            f"api_base={self.api_base}, model={self.model})")
    
    def get(self, key, default=None):
        return getattr(self, key, default)
    
    def copy(self):
        return self.__class__(**self.__dict__)
    
    def create(self, **kwargs):
        config = self.copy()
        for key, value in kwargs.items():
            if value is not None:
                setattr(config, key, value)
        return config
    
    def to_data(self, *kwargs):
        return {
            key: value for key, value in self.__dict__.items() if key in kwargs
        }

# OpenAI 专用配置
# core/config.py
class OpenAIConfig(Config):
    def __init__(
        self,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[list] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        # OpenAI 特定参数
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
        
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_base:
            self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        if not self.model:
            self.model = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
        if not self.headers:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

# Azure OpenAI 专用配置
class AzureOpenAIConfig(Config):
    def __init__(
        self,
        api_version: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[list] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        # Azure 特定参数
        self.api_version = api_version
        # OpenAI 兼容参数
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop

        # 从环境变量获取 Azure 配置
        if not self.api_key:
            self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if not self.api_base:
            self.api_base = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if not self.api_version:
            self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        if not self.model:
            self.model = os.getenv("AZURE_OPENAI_API_MODEL", "")
        
        # Azure 使用不同的请求头格式
        if not self.headers:
            self.headers = {
                "Content-Type": "application/json",
            }
        
        # update api_base
        """获取带 API 密钥的请求 URL"""
        endpoint = self.api_base.rstrip('/')
        if self.api_version:
            endpoint = f"{endpoint}?api-version={self.api_version}"
        if self.api_key:
            endpoint = f"{endpoint}&ak={self.api_key}"
        self.api_base = endpoint

# Anthropic 配置示例
class AnthropicConfig(Config):
    pass

