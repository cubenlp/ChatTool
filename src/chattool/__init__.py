"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '4.0.0'


from chattool.core import (
    Chat, OpenAIClient, AzureOpenAIClient,
     ChatResponse, Config, OpenAIConfig, AzureOpenAIConfig
)
from .const import OPENAI_API_BASE, OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_API_MODEL

try:
    import nest_asyncio
    nest_asyncio.apply()
except Exception as e:
    pass

__all__ = [
    "Chat",
    "OpenAIClient",
    "AzureOpenAIClient",
    "OPENAI_API_BASE",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_API_MODEL",
]