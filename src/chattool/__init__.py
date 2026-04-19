"""Top-level package for Chattool."""

import importlib

__author__ = """Rex Wang"""
__email__ = "1073853456@qq.com"
__version__ = "6.6.1"

from dotenv import load_dotenv

from .llm import Chat, AzureChat, ChatResponse
from .utils import (
    debug_log,
    load_envs,
    mask_secret,
    create_env_file,
    setup_logger,
    setup_jupyter_async,
    HTTPClient,
    HTTPConfig,
)
from .const import CHATTOOL_REPO_DIR, CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from .config import (
    OpenAIConfig,
    AzureConfig,
    AliyunConfig,
    TencentConfig,
    ZulipConfig,
    BaseEnvConfig,
)

setup_jupyter_async()
load_dotenv(CHATTOOL_REPO_DIR / ".env")

BaseEnvConfig.load_all(CHATTOOL_ENV_DIR, legacy_env_file=CHATTOOL_ENV_FILE)


_LAZY_ATTRS = {
    "LarkBot": ("chattool.tools.lark", "LarkBot"),
    "AliyunDNSClient": ("chattool.tools.dns", "AliyunDNSClient"),
    "TencentDNSClient": ("chattool.tools.dns", "TencentDNSClient"),
    "DynamicIPUpdater": ("chattool.tools.dns", "DynamicIPUpdater"),
    "SSLCertUpdater": ("chattool.tools.cert", "SSLCertUpdater"),
}


def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value


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
    "LarkBot",
    "AliyunDNSClient",
    "TencentDNSClient",
    "DynamicIPUpdater",
    "SSLCertUpdater",
]
