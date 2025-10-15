"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '4.0.0'


from chattool.core import (
    Chat, ChatBase, ChatAzure, ChatOpenAI, OpenAIClient, AzureOpenAIClient,
    HTTPClient, ChatResponse, Config, OpenAIConfig, AzureOpenAIConfig
)
from .const import OPENAI_API_BASE, OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_API_MODEL
from .utils import debug_log, load_envs, create_env_file

try:
    import nest_asyncio
    nest_asyncio.apply()
except Exception as e:
    pass

__all__ = [
    "Chat",
    "ChatBase",
    "ChatAzure",
    "ChatOpenAI",
    "OpenAIClient",
    "AzureOpenAIClient",
    "HTTPClient",
    "OPENAI_API_BASE",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_API_MODEL",
    "ChatResponse",
    "Config",
    "OpenAIConfig",
    "AzureOpenAIConfig",
    "debug_log",
    "load_envs",
    "create_env_file",
]