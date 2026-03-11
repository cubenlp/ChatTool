import click
import os
import ipaddress
import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
from pathlib import Path
from chattool.tools.network.scanner import ping_scan, port_scan
from chattool.tools.network.link_check import collect_urls, check_urls, check_service_url

@click.group()
def network():
    """Network scanning tools."""
    pass

@network.command()
@click.option('-net', '--network', required=True, help='Network segment to scan (e.g. 192.168.1.0/24)')
@click.option('-n', '--concurrency', default=50, help='Number of concurrent threads')
@click.option('-o', '--output', default=None, help='Output file path')
def ping(network, concurrency, output):
    """Scan a network for active hosts using ICMP ping."""
    ping_scan(network_segment=network, concurrency=concurrency, output_path=output)

@network.command()
@click.option('-i', '--input', required=False, help='Input file containing list of IPs')
@click.option('-net', '--network', required=False, help='Network segment to scan (e.g. 192.168.1.0/24)')
@click.option('-p', '--port', default=22, help='Port to scan (default: 22 for SSH)')
@click.option('-n', '--concurrency', default=50, help='Number of concurrent threads')
@click.option('-o', '--output', default=None, help='Output file path')
def ssh(input, network, port, concurrency, output):
    """Scan IPs for open SSH ports."""
    ip_list = []
    
    if input:
        if not os.path.exists(input):
            click.echo(f"Error: Input file '{input}' not found.")
            return
        with open(input, 'r') as f:
            ip_list = [line.strip() for line in f if line.strip()]
    elif network:
        try:
            net = ipaddress.ip_network(network, strict=False)
            ip_list = [str(ip) for ip in net.hosts()]
        except ValueError as e:
            click.echo(f"Error parsing network: {e}")
            return
    else:
        click.echo("Error: Either --input or --network must be provided.")
        return

    port_scan(ip_list=ip_list, port=port, concurrency=concurrency, output_path=output)


@network.command(name="links")
@click.option(
    "--path",
    "path_value",
    default=".",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    show_default=True,
    help="File or directory to scan for URLs.",
)
@click.option(
    "--glob",
    "globs",
    multiple=True,
    default=["*.md", "*.txt"],
    show_default=True,
    help="File glob patterns (used when --path is a directory).",
)
@click.option(
    "--url",
    "urls",
    multiple=True,
    help="Explicit URL(s) to check. If provided, scanning is skipped.",
)
@click.option("--filter", "filter_regex", default=None, help="Optional regex to filter URLs.")
@click.option("--timeout", default=6.0, show_default=True, help="Request timeout in seconds.")
def links(path_value, globs, urls, filter_regex, timeout):
    """Check URL validity from a file/directory or explicit list."""
    if urls:
        target_urls = list(urls)
    else:
        target_urls = collect_urls(path_value, globs)

    if filter_regex:
        pattern = re.compile(filter_regex)
        target_urls = [url for url in target_urls if pattern.search(url)]

    if not target_urls:
        click.echo("No URLs found.")
        return

    results = check_urls(target_urls, timeout=timeout)
    failed = 0
    for result in results:
        status = result.status if result.status is not None else "ERR"
        line = f"[{status}] {result.url} ({result.elapsed_ms}ms)"
        if result.ok:
            click.secho(line, fg="green")
        else:
            failed += 1
            if result.error:
                line = f"{line} - {result.error}"
            click.secho(line, fg="red")

    click.echo(f"Total: {len(results)}, OK: {len(results) - failed}, Failed: {failed}")
    if failed:
        raise SystemExit(2)


@network.command(name="services")
@click.option(
    "--chromium-url",
    default=None,
    show_default=False,
    help="Chromium service URL (or set CHATTOOL_CHROMIUM_URL).",
)
@click.option(
    "--chromium-token",
    default=None,
    show_default=False,
    help="Chromium token (or set CHATTOOL_CHROMIUM_TOKEN). If set, added as ?token=.",
)
@click.option(
    "--chromedriver-url",
    default=None,
    show_default=False,
    help="Chromedriver service URL (or set CHATTOOL_CHROMEDRIVER_URL).",
)
@click.option(
    "--playwright-url",
    default=None,
    show_default=False,
    help="Playwright service URL (or set CHATTOOL_PLAYWRIGHT_URL).",
)
@click.option("--timeout", default=6.0, show_default=True, help="Request timeout in seconds.")
def services(chromium_url, chromium_token, chromedriver_url, playwright_url, timeout):
    """Check that chromium/chromedriver/playwright URLs respond with expected content."""
    chromium_url = chromium_url or os.getenv("CHATTOOL_CHROMIUM_URL")
    chromedriver_url = chromedriver_url or os.getenv("CHATTOOL_CHROMEDRIVER_URL")
    playwright_url = playwright_url or os.getenv("CHATTOOL_PLAYWRIGHT_URL")
    chromium_token = chromium_token or os.getenv("CHATTOOL_CHROMIUM_TOKEN")

    missing = [
        name for name, value in [
            ("chromium", chromium_url),
            ("chromedriver", chromedriver_url),
            ("playwright", playwright_url),
        ] if not value
    ]
    if missing:
        click.secho(
            "Missing service URL(s): "
            + ", ".join(missing)
            + ". Provide --<service>-url or set CHATTOOL_*_URL env vars.",
            fg="red",
        )
        raise SystemExit(2)

    if chromium_token:
        chromium_url = _append_token(chromium_url, chromium_token)

    targets = [
        ("chromium", chromium_url),
        ("chromedriver", chromedriver_url),
        ("playwright", playwright_url),
    ]

    failed = 0
    for expected, url in targets:
        result = check_service_url(url, expected, timeout=timeout)
        status = result.status if result.status is not None else "ERR"
        line = f"[{status}] {expected}: {result.url} ({result.elapsed_ms}ms)"
        if result.ok:
            click.secho(line, fg="green")
        else:
            failed += 1
            if result.error:
                line = f"{line} - {result.error}"
            click.secho(line, fg="red")

    click.echo(f"Total: {len(targets)}, OK: {len(targets) - failed}, Failed: {failed}")
    if failed:
        raise SystemExit(2)


def _append_token(url: str, token: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "token" in query:
        return url
    query["token"] = [token]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

if __name__ == '__main__':
    network()
