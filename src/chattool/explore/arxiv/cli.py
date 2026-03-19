"""arXiv explore CLI commands."""
import click
from datetime import date


def _fmt_paper(p, verbose: bool = False) -> str:
    authors = ", ".join(p.authors[:3]) + (" et al." if len(p.authors) > 3 else "")
    lines = [
        f"[{p.arxiv_id}] {p.title}",
        f"  {authors}",
        f"  {p.primary_category} | {p.published.strftime('%Y-%m-%d')} | {p.url}",
    ]
    if verbose and p.summary:
        summary = p.summary.replace("\n", " ")[:200].strip()
        lines.append(f"  {summary}...")
    return "\n".join(lines)


@click.group(name="arxiv")
def arxiv_cli():
    """arXiv paper search and daily digest."""
    pass


@arxiv_cli.command("search")
@click.argument("query")
@click.option("-n", "--max-results", default=10, show_default=True, help="Max number of results.")
@click.option("-c", "--category", multiple=True, help="Filter by category (e.g. cs.AI). Repeatable.")
@click.option("-k", "--keyword", multiple=True, help="Filter results by keyword. Repeatable.")
@click.option("--sort", default="submittedDate", show_default=True,
              type=click.Choice(["submittedDate", "lastUpdatedDate", "relevance"]),
              help="Sort criterion.")
@click.option("-v", "--verbose", is_flag=True, help="Show abstract excerpt.")
def search_cmd(query, max_results, category, keyword, sort, verbose):
    """Search arXiv papers by QUERY string.

    QUERY supports arXiv field prefixes: ti:, au:, abs:, cat:, all:

    \b
    Examples:
      chattool explore arxiv search "cat:cs.AI AND ti:transformer"
      chattool explore arxiv search "all:diffusion" -c cs.CV -n 20
    """
    from chattool.explore.arxiv import ArxivClient
    client = ArxivClient()
    papers = client.search(query, max_results=max_results, sort_by=sort)
    if category:
        papers = client.filter_papers(papers, categories=list(category))
    if keyword:
        papers = client.filter_papers(papers, keywords=list(keyword))
    if not papers:
        click.echo("No papers found.")
        return
    click.echo(f"Found {len(papers)} paper(s):\n")
    for p in papers:
        click.echo(_fmt_paper(p, verbose=verbose))
        click.echo()


@arxiv_cli.command("daily")
@click.option("-c", "--category", multiple=True, required=True,
              help="Category to fetch (e.g. cs.AI). Repeatable.")
@click.option("-k", "--keyword", multiple=True, help="Filter by keyword. Repeatable.")
@click.option("--days", default=1, show_default=True, help="Fetch papers from last N days.")
@click.option("-n", "--max-results", default=200, show_default=True)
@click.option("-v", "--verbose", is_flag=True, help="Show abstract excerpt.")
def daily_cmd(category, keyword, days, max_results, verbose):
    """Fetch latest arXiv submissions.

    \b
    Examples:
      chattool explore arxiv daily -c cs.AI -c cs.LG
      chattool explore arxiv daily -c cs.CV -k diffusion --days 3
    """
    from chattool.explore.arxiv import DailyFetcher
    fetcher = DailyFetcher()
    papers = fetcher.since(
        days=days,
        categories=list(category),
        keywords=list(keyword) or None,
        max_results=max_results,
    )
    if not papers:
        click.echo("No papers found.")
        return
    label = "today" if days == 1 else f"last {days} days"
    click.echo(f"{len(papers)} paper(s) from {label}:\n")
    for p in papers:
        click.echo(_fmt_paper(p, verbose=verbose))
        click.echo()


@arxiv_cli.command("get")
@click.argument("arxiv_id")
@click.option("-v", "--verbose", is_flag=True, help="Show full abstract.")
def get_cmd(arxiv_id, verbose):
    """Fetch a single paper by arXiv ID.

    \b
    Example:
      chattool explore arxiv get 1706.03762
    """
    from chattool.explore.arxiv import ArxivClient
    client = ArxivClient()
    try:
        p = client.get_by_id(arxiv_id)
    except StopIteration:
        click.echo(f"Paper {arxiv_id!r} not found.", err=True)
        raise SystemExit(1)
    click.echo(_fmt_paper(p, verbose=True))
    if verbose:
        click.echo(f"\nAbstract:\n{p.summary}")
