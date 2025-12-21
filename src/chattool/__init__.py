"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '4.2.0'


from chattool.core import (
    Chat, AzureChat, HTTPClient, ChatResponse, HTTPConfig,
)
from .const import OPENAI_API_BASE, OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_API_MODEL
from .utils import debug_log, load_envs, create_env_file
import asyncio

def setup_jupyter_async():
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            import nest_asyncio
            loop = asyncio.get_running_loop()
            if not hasattr(loop, '_nest_asyncio_patched'):
                nest_asyncio.apply()
                # 标记已经应用过
                loop._nest_asyncio_patched = True
    except Exception:
        pass

setup_jupyter_async()

__all__ = [
    "Chat",
    "AzureChat",
    "HTTPClient",
    "OPENAI_API_BASE",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_API_MODEL",
    "ChatResponse",
    "HTTPConfig",
    "debug_log",
    "load_envs",
    "create_env_file",
]