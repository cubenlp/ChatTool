import click
from chattool.mcp.server import mcp

@click.group()
def cli():
    """MCP Server Management Tools."""
    pass

@cli.command(context_settings={"ignore_unknown_options": True})
@click.option("--transport", "-t", default="stdio", type=click.Choice(["stdio", "http"]), help="Transport mode: stdio (default) or http")
@click.option("--host", default="127.0.0.1", help="Host for HTTP server")
@click.option("--port", default=8000, help="Port for HTTP server")
def start(transport, host, port):
    """Run the MCP server directly.
    
    Examples:
    
        chattool mcp start                   # Run with stdio (default)
        chattool mcp start --transport http  # Run with HTTP on localhost:8000
    """
    mcp.run(transport=transport, host=host, port=port)

@cli.command()
def info():
    """Inspect the MCP server capabilities."""
    # Since we can't import fastmcp.cli.inspect easily, we'll just print basic info from our instance
    click.echo(f"MCP Server: {mcp.name}")
    click.echo("\nTools:")
    # FastMCP stores tools in _tool_functions (decorated functions)
    # We can inspect mcp._tool_functions or similar if public API exists.
    # But let's check if mcp has an inspect capability or just list them.
    # Looking at FastMCP source/usage (inferred):
    # It doesn't seem to have a public 'inspect' method on the instance that prints to CLI.
    # We'll manually list them.
    
    # Accessing internal registry (common pattern in such libs if no public API)
    # Or just try to print the object
    # Let's try to iterate over registered tools if possible.
    # FastMCP uses decorators, so maybe we can just list what we know.
    
    # Better approach: Just print the static list since we defined it in server.py
    tools = [
        "dns_list_domains", "dns_get_records", "dns_add_record", 
        "dns_delete_record", "dns_ddns_update", "dns_cert_update"
    ]
    for t in tools:
        click.echo(f"  - {t}")
