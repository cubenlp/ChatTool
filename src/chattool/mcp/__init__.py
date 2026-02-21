from .server import mcp

def main():
    """Entry point for the MCP server."""
    if mcp is None:
        print("Error: FastMCP is not installed. This functionality requires Python 3.10+.")
        return
    mcp.run()

__all__ = ["mcp", "main"]
