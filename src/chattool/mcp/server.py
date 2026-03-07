import os
try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None
from chattool.utils import setup_logger
from chattool.mcp import zulip, dns, network

logger = setup_logger("mcp_server", log_level="INFO")
SERVER_NAME = "ChatTool MCP Server"

if FastMCP:
    mcp = FastMCP(SERVER_NAME)
    for register in (zulip.register, dns.register, network.register):
        register(mcp)
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
