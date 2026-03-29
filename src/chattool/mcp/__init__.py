import sys


def __getattr__(name: str):
    if name != "mcp":
        raise AttributeError(name)
    from .server import mcp as server_mcp

    globals()["mcp"] = server_mcp
    return server_mcp


def main():
    """Entry point for the MCP server."""
    from .server import mcp

    if mcp is None:
        print("Error: MCP server is not available. Please install 'fastmcp' (requires Python >= 3.10).", file=sys.stderr)
        sys.exit(1)
    mcp.run()

__all__ = ["mcp", "main"]
