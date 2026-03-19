"""explore CLI — top-level group."""
import click
from chattool.client.main import LazyGroup


@click.group(name="explore", cls=LazyGroup)
def explore_cli():
    """Explore external data sources: arxiv, github, wordpress."""
    pass


explore_cli._lazy_commands = {
    "arxiv": lambda: _load_arxiv(),
}


def _load_arxiv():
    from chattool.explore.arxiv.cli import arxiv_cli
    return arxiv_cli
