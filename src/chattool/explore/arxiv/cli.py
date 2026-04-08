"""arXiv explore CLI commands."""

from __future__ import annotations

import click

from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)


ARXIV_GET_SCHEMA = CommandSchema(
    name="arxiv-get",
    fields=(CommandField("arxiv_id", prompt="arxiv id", required=True),),
)


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


def _resolve_preset(preset_name, categories, keywords):
    """Merge preset config with explicit -c/-k overrides."""
    from chattool.explore.arxiv import PRESETS

    cats = list(categories)
    kws = list(keywords)
    if preset_name:
        if preset_name not in PRESETS:
            raise click.BadParameter(
                f"Unknown preset '{preset_name}'. Available: {', '.join(PRESETS)}"
            )
        p = PRESETS[preset_name]
        cats = cats or p.categories
        kws = kws or p.keywords
    return cats, kws


@click.group(name="arxiv")
def arxiv_cli():
    """arXiv paper search and daily digest."""
    pass


@arxiv_cli.command("search")
@click.argument("query", required=False, default=None)
@click.option("-p", "--preset", default=None, help="Use a named preset (e.g. ai4math).")
@click.option(
    "-n", "--max-results", default=10, show_default=True, help="Max number of results."
)
@click.option(
    "-c",
    "--category",
    multiple=True,
    help="Filter by category (e.g. cs.AI). Repeatable.",
)
@click.option(
    "-k", "--keyword", multiple=True, help="Filter results by keyword. Repeatable."
)
@click.option(
    "--sort",
    default="submittedDate",
    show_default=True,
    type=click.Choice(["submittedDate", "lastUpdatedDate", "relevance"]),
    help="Sort criterion.",
)
@click.option("-v", "--verbose", is_flag=True, help="Show abstract excerpt.")
def search_cmd(query, preset, max_results, category, keyword, sort, verbose):
    """Search arXiv papers by QUERY string or preset.

    QUERY supports arXiv field prefixes: ti:, au:, abs:, cat:, all:

    \b
    Examples:
      chattool explore arxiv search "cat:cs.AI AND ti:transformer"
      chattool explore arxiv search -p ai4math -n 20
      chattool explore arxiv search "all:diffusion" -c cs.CV -n 20
    """
    from chattool.explore.arxiv import ArxivClient, build_query

    cats, kws = _resolve_preset(preset, category, keyword)

    if not query:
        if not cats and not kws:
            raise click.UsageError("Provide a QUERY or use --preset / -c / -k.")
        query = build_query(categories=cats, keywords=kws)
        cats, kws = [], []  # already baked into query

    client = ArxivClient()
    papers = client.search(query, max_results=max_results, sort_by=sort)
    if cats:
        papers = client.filter_papers(papers, categories=cats)
    if kws:
        papers = client.filter_papers(papers, keywords=kws)
    if not papers:
        click.echo("No papers found.")
        return
    click.echo(f"Found {len(papers)} paper(s):\n")
    for p in papers:
        click.echo(_fmt_paper(p, verbose=verbose))
        click.echo()


@arxiv_cli.command("daily")
@click.option("-p", "--preset", default=None, help="Use a named preset (e.g. ai4math).")
@click.option(
    "-c",
    "--category",
    multiple=True,
    help="Category to fetch (e.g. cs.AI). Repeatable.",
)
@click.option("-k", "--keyword", multiple=True, help="Filter by keyword. Repeatable.")
@click.option(
    "--days", default=1, show_default=True, help="Fetch papers from last N days."
)
@click.option("-n", "--max-results", default=200, show_default=True)
@click.option("-v", "--verbose", is_flag=True, help="Show abstract excerpt.")
def daily_cmd(preset, category, keyword, days, max_results, verbose):
    """Fetch latest arXiv submissions.

    \b
    Examples:
      chattool explore arxiv daily -p ai4math
      chattool explore arxiv daily -c cs.AI -c cs.LG
      chattool explore arxiv daily -p math-formalization --days 3 -v
    """
    from chattool.explore.arxiv import DailyFetcher

    cats, kws = _resolve_preset(preset, category, keyword)
    if not cats and not kws:
        raise click.UsageError("Provide --preset or at least one -c category.")

    fetcher = DailyFetcher()
    raw = fetcher.since(
        days=days,
        categories=cats or None,
        keywords=kws or None,
        max_results=max_results,
    )
    # If using a preset, apply its strict client-side filter
    from chattool.explore.arxiv import PRESETS

    if preset and preset in PRESETS:
        papers = PRESETS[preset].filter(raw)
    else:
        papers = raw
    if not papers:
        click.echo("No papers found.")
        return
    label = "today" if days == 1 else f"last {days} days"
    click.echo(f"{len(papers)} paper(s) from {label}:\n")
    for p in papers:
        click.echo(_fmt_paper(p, verbose=verbose))
        click.echo()


@arxiv_cli.command("get")
@click.argument("arxiv_id", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Show full abstract.")
@add_interactive_option
def get_cmd(arxiv_id, verbose, interactive):
    """Fetch a single paper by arXiv ID.

    \b
    Example:
      chattool explore arxiv get 1706.03762
    """
    from chattool.explore.arxiv import ArxivClient

    inputs = resolve_command_inputs(
        schema=ARXIV_GET_SCHEMA,
        provided={"arxiv_id": arxiv_id},
        interactive=interactive,
        usage="Usage: chattool explore arxiv get [ARXIV_ID] [-i|-I]",
    )
    arxiv_id = inputs["arxiv_id"]

    client = ArxivClient()
    try:
        p = client.get_by_id(arxiv_id)
    except StopIteration:
        click.echo(f"Paper {arxiv_id!r} not found.", err=True)
        raise SystemExit(1)
    click.echo(_fmt_paper(p, verbose=True))
    if verbose:
        click.echo(f"\nAbstract:\n{p.summary}")


@arxiv_cli.command("presets")
def presets_cmd():
    """List available search presets."""
    from chattool.explore.arxiv import PRESETS

    for name, p in PRESETS.items():
        click.echo(f"{name}")
        click.echo(f"  {p.description}")
        click.echo(f"  categories: {', '.join(p.categories)}")
        click.echo(f"  keywords:   {len(p.keywords)} terms")
        click.echo()
