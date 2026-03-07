import json
import sys
import click
from chattool.mcp.catalog import get_visible_tool_specs
from chattool.mcp.server import mcp
try:
    from chattool.mcp.skills import get_skill, load_skills
    _SKILLS_MODULE_AVAILABLE = True
except ImportError:
    _SKILLS_MODULE_AVAILABLE = False


def _ensure_skills_module_available():
    if not _SKILLS_MODULE_AVAILABLE:
        click.echo("Error: skills module is temporarily unavailable.", err=True)
        click.echo("Please add `chattool.mcp.skills` back before using `chattool mcp skills`.", err=True)
        sys.exit(1)

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
    if mcp is None:
        click.echo("Error: MCP server is not available. Please install 'fastmcp' (requires Python >= 3.10).", err=True)
        sys.exit(1)
    mcp.run(transport=transport, host=host, port=port)

@cli.command()
@click.option("--json-output", is_flag=True, help="Output in JSON format.")
def info(json_output):
    """Inspect the MCP server capabilities."""
    if mcp is None:
        click.echo("Error: MCP server is not available. Please install 'fastmcp' (requires Python >= 3.10).", err=True)
        sys.exit(1)

    include_tags = getattr(mcp, "include_tags", None) or set()
    exclude_tags = getattr(mcp, "exclude_tags", None) or set()
    enabled_tags = [v.strip() for v in include_tags if v and v.strip()]
    disabled_tags = [v.strip() for v in exclude_tags if v and v.strip()]
    tools = get_visible_tool_specs(enable_tags=enabled_tags, disable_tags=disabled_tags)
    if json_output:
        payload = {
            "name": mcp.name,
            "tool_count": len(tools),
            "enabled_tags": sorted(enabled_tags),
            "disabled_tags": sorted(disabled_tags),
            "tools": [
                {
                    "name": item.name,
                    "module": item.module,
                    "tags": list(item.tags),
                    "summary": item.summary,
                }
                for item in tools
            ],
        }
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"MCP Server: {mcp.name}")
    click.echo(f"Visible Tools: {len(tools)}")
    if enabled_tags:
        click.echo(f"Enabled Tags: {', '.join(sorted(enabled_tags))}")
    if disabled_tags:
        click.echo(f"Disabled Tags: {', '.join(sorted(disabled_tags))}")
    click.echo("")
    for item in tools:
        click.echo(f"- {item.name} [{', '.join(item.tags)}] ({item.module})")


@cli.command(name="inspect")
@click.option("--json-output", is_flag=True, help="Output in JSON format.")
def inspect(json_output):
    """Backward-compatible alias of `chattool mcp info`."""
    ctx = click.get_current_context()
    ctx.invoke(info, json_output=json_output)


@cli.group()
def skills():
    """Inspect bundled skill manifests."""
    pass


@skills.command("list")
@click.option("--lang", default="zh", type=click.Choice(["zh", "en"]), help="Preferred skill language.")
@click.option("--json-output", is_flag=True, help="Output in JSON format.")
def skills_list(lang, json_output):
    _ensure_skills_module_available()
    items = load_skills(lang=lang)
    if json_output:
        payload = [
            {
                "name": item.name,
                "description": item.description,
                "language": item.language,
                "skill_dir": item.skill_dir,
                "file_path": item.file_path,
            }
            for item in items
        ]
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"Skills: {len(items)}")
    for item in items:
        desc = item.description or "No description"
        click.echo(f"- {item.name} ({item.skill_dir}, {item.language})")
        click.echo(f"  {desc}")


@skills.command("show")
@click.argument("name")
@click.option("--lang", default="zh", type=click.Choice(["zh", "en"]), help="Preferred skill language.")
def skills_show(name, lang):
    _ensure_skills_module_available()
    item = get_skill(name=name, lang=lang)
    if item is None:
        click.echo(f"Skill not found: {name}", err=True)
        sys.exit(1)
    click.echo(f"Name: {item.name}")
    click.echo(f"Directory: {item.skill_dir}")
    click.echo(f"Language: {item.language}")
    click.echo(f"Manifest: {item.file_path}")
    click.echo("")
    click.echo(item.content)
