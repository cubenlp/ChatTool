import importlib
import os

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from chattool.utils import setup_logger

logger = setup_logger("mcp_server", log_level="INFO")
SERVER_NAME = "ChatTool MCP Server"
REGISTER_MODULES = (
    "chattool.tools.zulip.mcp",
    "chattool.tools.dns.mcp",
    "chattool.tools.network.mcp",
)


def _register_optional_tools(mcp_instance):
    for module_name in REGISTER_MODULES:
        try:
            register = getattr(importlib.import_module(module_name), "register")
        except ImportError as exc:
            logger.warning(f"Skipping MCP module {module_name}: {exc}")
            continue
        register(mcp_instance)

if FastMCP:
    mcp = FastMCP(SERVER_NAME)
    _register_optional_tools(mcp)
else:
    mcp = None
    logger.warning("FastMCP module not found. MCP functionality will be disabled.")

def _configure_visibility():
    """Configure tool visibility based on environment variables."""
    if mcp is None:
        return

    enable_tags_str = os.getenv("CHATTOOL_MCP_ENABLE_TAGS")
    disable_tags_str = os.getenv("CHATTOOL_MCP_DISABLE_TAGS")

    if enable_tags_str:
        tags = {t.strip() for t in enable_tags_str.split(",") if t.strip()}
        if tags:
            logger.info(f"Enabling only tools with tags: {tags}")
            mcp.include_tags = tags
    
    if disable_tags_str:
        tags = {t.strip() for t in disable_tags_str.split(",") if t.strip()}
        if tags:
            logger.info(f"Disabling tools with tags: {tags}")
            mcp.exclude_tags = tags

_configure_visibility()
