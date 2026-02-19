import os
from fastmcp import FastMCP
from chattool.utils import setup_logger
from chattool.mcp import zulip, dns

# Initialize FastMCP server
mcp = FastMCP("ChatTool DNS Manager")

# Logger for MCP tools
logger = setup_logger("mcp_server", log_level="INFO")

# Register Modules
zulip.register(mcp)
dns.register(mcp)

# --- Configuration & Visibility ---

def _configure_visibility():
    """Configure tool visibility based on environment variables."""
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

# Apply configuration
_configure_visibility()
