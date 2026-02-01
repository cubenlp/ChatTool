from .server import mcp

def main():
    """Entry point for the MCP server."""
    mcp.run()

__all__ = ["mcp", "main"]
