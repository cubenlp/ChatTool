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
        self.headers = headers
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__post__init__()

    def __post__init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}
    
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
class OpenAIConfig(Config):
    def __post__init__(self):
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
        

# Anthropic 配置示例
class AnthropicConfig(Config):
    pass

# Azure OpenAI 配置示例  
class AzureConfig(Config):
    pass


