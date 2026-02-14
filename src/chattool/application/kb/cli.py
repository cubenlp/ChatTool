import click
from typing import Optional
from chattool.application.kb.manager import KBManager
import datetime
import os

@click.group()
def cli():
    """Knowledge Base Management (ZulipKB)."""
    pass

@cli.command()
@click.argument('name', required=False)
def init(name: Optional[str]):
    """Initialize a new knowledge base workspace."""
    manager = KBManager(name)
    click.echo(f"Initialized workspace '{manager.name}' at {manager.db_path}")

@cli.command()
@click.argument('name', required=False)
@click.argument('stream')
def track(name: Optional[str], stream: str):
    """Track a Zulip stream in the workspace."""
    manager = KBManager(name)
    manager.track_stream(stream)

@cli.command()
@click.argument('name', required=False)
@click.argument('stream')
def untrack(name: Optional[str], stream: str):
    """Stop tracking a Zulip stream."""
    manager = KBManager(name)
    manager.untrack_stream(stream)

@cli.command()
@click.argument('name', required=False)
@click.option('--latest', is_flag=True, help="Fetch latest messages only (snapshot mode)")
@click.option('--limit', default=1000, help="Max messages to fetch (default 1000)")
def sync(name: Optional[str], latest: bool, limit: int):
    """Sync tracked streams from Zulip."""
    manager = KBManager(name)
    mode = "snapshot (latest)" if latest else "incremental"
    click.echo(f"Syncing workspace '{manager.name}' in {mode} mode...")
    manager.sync(fetch_newest=latest, limit=limit)
    click.echo("Sync completed.")

@cli.command()
@click.argument('name', required=False)
@click.option('--stream', help="Filter by stream")
@click.option('--export', help="Export to file (CSV)")
def list(name: Optional[str], stream: Optional[str], export: Optional[str]):
    """List topics in the workspace."""
    manager = KBManager(name)
    
    if export:
        manager.export_topics(export)
        click.echo(f"Topics exported to {export}")
        return

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
@click.argument('name', required=False)
@click.argument('stream')
@click.argument('topic')
@click.option('--limit', default=50, help="Number of messages to show")
@click.option('--export', help="Export to file (TXT)")
def show(name: Optional[str], stream: str, topic: str, limit: int, export: Optional[str]):
    """Show messages in a topic."""
    manager = KBManager(name)
    
    if export:
        manager.export_messages(stream, topic, export)
        click.echo(f"Messages exported to {export}")
        return

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
@click.argument('name', required=False)
@click.argument('query')
def search(name: Optional[str], query: str):
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

@cli.command()
@click.argument('name', required=False)
@click.argument('stream')
@click.argument('topic')
@click.option('--to-stream', required=True, help="Target stream to post result")
@click.option('--to-topic', required=True, help="Target topic to post result")
def process(name: Optional[str], stream: str, topic: str, to_stream: str, to_topic: str):
    """Process a topic and repost summary (Demo: Uppercase)."""
    manager = KBManager(name)
    
    def simple_processor(text):
        return f"**Knowledge Summary for {topic}**\n\n{text[:500]}...\n\n(Processed at {datetime.datetime.now()})"

    click.echo(f"Processing topic '{topic}' in stream '{stream}'...")
    result = manager.process_topic(stream, topic, simple_processor)
    
    click.echo(f"Reposting to '{to_stream}' > '{to_topic}'...")
    manager.repost_knowledge(to_stream, to_topic, result)
    click.echo("Done.")
