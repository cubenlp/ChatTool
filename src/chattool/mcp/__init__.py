from .server import mcp
import sys

def main():
    """Entry point for the MCP server."""
    if mcp is None:
        print("Error: MCP server is not available. Please install 'fastmcp' (requires Python >= 3.10).", file=sys.stderr)
        sys.exit(1)
    mcp.run()

__all__ = ["mcp", "main"]
