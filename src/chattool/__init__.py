"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '5.1.0'

from dotenv import load_dotenv

from .llm import Chat, AzureChat, ChatResponse
from .utils import (
    debug_log, load_envs, mask_secret,
    create_env_file, setup_logger, setup_jupyter_async,
    HTTPClient, HTTPConfig
)
from .const import CHATTOOL_REPO_DIR
from .config import OpenAIConfig, AzureConfig, AliyunConfig, TencentConfig, ZulipConfig

setup_jupyter_async()
load_dotenv(CHATTOOL_REPO_DIR / '.env')


__all__ = [
    "Chat",
    "AzureChat",
    "HTTPClient",
    "ChatResponse",
    "HTTPConfig",
    "debug_log",
    "create_env_file",
    "mask_secret",
    "setup_logger",
    "OpenAIConfig",
    "AzureConfig",
    "AliyunConfig",
    "TencentConfig",
    "ZulipConfig",
]