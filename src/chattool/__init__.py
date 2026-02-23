"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '5.0.0'


from chattool.llm import (
    Chat, AzureChat, ChatResponse
)
from .utils import (
    debug_log, load_envs,
    create_env_file, setup_logger, setup_jupyter_async,
    HTTPClient, HTTPConfig
)

setup_jupyter_async()

__all__ = [
    "Chat",
    "AzureChat",
    "HTTPClient",
    "ChatResponse",
    "HTTPConfig",
    "debug_log",
    "create_env_file",
    "setup_logger",
]