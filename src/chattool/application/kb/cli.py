import click
from typing import Optional
from chattool.application.kb.manager import KBManager
import datetime

@click.group()
def cli():
    """Knowledge Base Management (ZulipKB)."""
    pass

@cli.command()
@click.argument('name')
def init(name: str):
    """Initialize a new knowledge base workspace."""
    manager = KBManager(name)
    click.echo(f"Initialized workspace '{name}' at {manager.db_path}")

@cli.command()
@click.argument('name')
@click.argument('stream')
def track(name: str, stream: str):
    """Track a Zulip stream in the workspace."""
    manager = KBManager(name)
    manager.track_stream(stream)

@cli.command()
@click.argument('name')
@click.argument('stream')
def untrack(name: str, stream: str):
    """Stop tracking a Zulip stream."""
    manager = KBManager(name)
    manager.untrack_stream(stream)

@cli.command()
@click.argument('name')
def sync(name: str):
    """Sync tracked streams from Zulip."""
    manager = KBManager(name)
    click.echo(f"Syncing workspace '{name}'...")
    manager.sync()
    click.echo("Sync completed.")

@cli.command()
@click.argument('name')
@click.option('--stream', help="Filter by stream")
def list(name: str, stream: Optional[str]):
    """List topics in the workspace."""
    manager = KBManager(name)
    topics = manager.list_topics(stream)
    
    if not topics:
        click.echo("No topics found.")
        return

    # Print table header
    click.echo(f"{'Stream':<20} | {'Topic':<40} | {'Count':<5}")
    click.echo("-" * 70)
    
    for s, t, c in topics:
        # Truncate if too long
        s_disp = (s[:17] + '...') if len(s) > 20 else s
        t_disp = (t[:37] + '...') if len(t) > 40 else t
        click.echo(f"{s_disp:<20} | {t_disp:<40} | {c:<5}")

@cli.command()
@click.argument('name')
@click.argument('stream')
@click.argument('topic')
@click.option('--limit', default=50, help="Number of messages to show")
def show(name: str, stream: str, topic: str, limit: int):
    """Show messages in a topic."""
    manager = KBManager(name)
    messages = manager.get_messages(stream, topic, limit)
    
    if not messages:
        click.echo("No messages found.")
        return
        
    for msg in messages:
        dt = datetime.datetime.fromtimestamp(msg.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        click.echo(f"[{dt}] {msg.sender}:")
        click.echo(f"{msg.content}")
        click.echo("-" * 40)

@cli.command()
@click.argument('name')
@click.argument('query')
def search(name: str, query: str):
    """Search messages in the workspace."""
    manager = KBManager(name)
    results = manager.search(query)
    
    if not results:
        click.echo("No matches found.")
        return
        
    for msg in results:
        dt = datetime.datetime.fromtimestamp(msg.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        click.echo(f"[{dt}] {msg.stream} > {msg.topic}")
        click.echo(f"{msg.sender}: {msg.content[:100]}...")
        click.echo("-" * 40)
