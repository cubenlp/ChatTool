import json
from typing import Optional
import click

from chattool.config.github import GitHubConfig

_ENV_LOADED = False


@click.group(name="gh")
def cli():
    """GitHub helpers (PR, issues)."""
    pass


@cli.command(name="pr-create")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--base", required=True, help="Base branch (e.g., main, vibe-master).")
@click.option("--head", required=True, help="Head branch (e.g., feature-branch or owner:branch).")
@click.option("--title", required=True, help="Pull request title.")
@click.option("--body", default="", help="Pull request body.")
@click.option(
    "--body-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Read PR body from file (overrides --body).",
)
@click.option(
    "--token",
    default=None,
    help="GitHub token (or set GITHUB_ACCESS_TOKEN).",
)
def pr_create(repo, base, head, title, body, body_file, token):
    """Create a GitHub pull request."""
    from github import Github
    from github.GithubException import GithubException

    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            body = handle.read()

    repo = _resolve_repo(repo)
    client = _get_client(token, require_token=True)
    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.create_pull(title=title, body=body, base=base, head=head)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    click.echo(f"PR created: {pr.html_url}")


@cli.command(name="pr-list")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--state", default="open", type=click.Choice(["open", "closed", "all"]), show_default=True)
@click.option("--limit", default=20, type=int, show_default=True, help="Max PRs to show.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_list(repo, state, limit, json_output, token):
    """List pull requests."""
    from github import Github
    from github.GithubException import GithubException

    client = _get_client(token)
    repo = _resolve_repo(repo)
    try:
        repo_obj = client.get_repo(repo)
        pulls = repo_obj.get_pulls(state=state, sort="updated", direction="desc")
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    items = []
    for pr in pulls:
        items.append({
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "url": pr.html_url,
            "author": pr.user.login if pr.user else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            "base": pr.base.ref if pr.base else None,
            "head": pr.head.ref if pr.head else None,
        })
        if len(items) >= limit:
            break

    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not items:
        click.echo("No pull requests found.")
        return

    for item in items:
        click.echo(f"#{item['number']} [{item['state']}] {item['title']} ({item['author']})")
        click.echo(f"  {item['url']}")


@cli.command(name="pr-view")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--number", required=True, type=int, help="Pull request number.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_view(repo, number, json_output, token):
    """Show pull request details."""
    from github import Github
    from github.GithubException import GithubException

    client = _get_client(token)
    repo = _resolve_repo(repo)
    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.get_pull(number)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    payload = {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "url": pr.html_url,
        "author": pr.user.login if pr.user else None,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        "base": pr.base.ref if pr.base else None,
        "head": pr.head.ref if pr.head else None,
    }

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"#{payload['number']} [{payload['state']}] {payload['title']}")
    click.echo(f"Author: {payload['author']}")
    click.echo(f"URL: {payload['url']}")
    click.echo(f"Base: {payload['base']}  Head: {payload['head']}")
    click.echo(f"Created: {payload['created_at']}  Updated: {payload['updated_at']}")
    click.echo(f"Merged: {payload['merged_at']}")


@cli.command(name="pr-comment")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--number", required=True, type=int, help="Pull request number.")
@click.option("--body", required=True, help="Comment body.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_comment(repo, number, body, token):
    """Add a comment to a pull request."""
    from github import Github
    from github.GithubException import GithubException

    client = _get_client(token, require_token=True)
    repo = _resolve_repo(repo)
    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.get_pull(number)
        comment = pr.create_issue_comment(body)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    click.echo(f"Comment created: {comment.html_url}")


@cli.command(name="pr-merge")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--number", required=True, type=int, help="Pull request number.")
@click.option("--method", default="merge", type=click.Choice(["merge", "squash", "rebase"]), show_default=True)
@click.option("--title", default=None, help="Optional merge title.")
@click.option("--message", default=None, help="Optional merge message.")
@click.option("--confirm", is_flag=True, help="Confirm merge without prompt.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_merge(repo, number, method, title, message, confirm, token):
    """Merge a pull request."""
    from github import Github
    from github.GithubException import GithubException

    client = _get_client(token, require_token=True)
    repo = _resolve_repo(repo)
    if not confirm and not click.confirm(f"Merge PR #{number} in {repo} using {method}?", default=False):
        click.echo("Cancelled.")
        return

    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.get_pull(number)
        payload = {"merge_method": method}
        if title is not None:
            payload["commit_title"] = title
        if message is not None:
            payload["commit_message"] = message
        result = pr.merge(**payload)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    if not result.merged:
        raise click.ClickException(f"Merge failed: {result.message}")

    click.echo(f"PR merged: {pr.html_url}")


@cli.command(name="pr-update")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--number", required=True, type=int, help="Pull request number.")
@click.option("--title", default=None, help="New pull request title.")
@click.option("--body", default=None, help="New pull request body.")
@click.option(
    "--body-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Read PR body from file (overrides --body).",
)
@click.option("--state", default=None, type=click.Choice(["open", "closed"]), help="Set PR state.")
@click.option("--base", default=None, help="Change base branch.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_update(repo, number, title, body, body_file, state, base, token):
    """Update pull request metadata (title/body/state/base)."""
    from github import Github
    from github.GithubException import GithubException

    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            body = handle.read()

    if title is None and body is None and state is None and base is None:
        raise click.ClickException("No updates provided. Use --title/--body/--state/--base.")

    client = _get_client(token, require_token=True)
    repo = _resolve_repo(repo)
    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.get_pull(number)
        payload = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if base is not None:
            payload["base"] = base
        pr.edit(**payload)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    click.echo(f"PR updated: {pr.html_url}")


def _get_client(token: Optional[str], require_token: bool = False):
    from github import Github, Auth

    token = token or GitHubConfig.GITHUB_ACCESS_TOKEN.value
    if require_token and not token:
        raise click.ClickException("Missing token. Set GITHUB_ACCESS_TOKEN or pass --token.")
    if not token:
        click.secho("Warning: no token provided; GitHub API rate limits may apply.", fg="yellow")
        return Github()
    return Github(auth=Auth.Token(token))


def _resolve_repo(repo: Optional[str]) -> str:
    repo = repo or GitHubConfig.GITHUB_DEFAULT_REPO.value
    if not repo:
        raise click.ClickException("Missing repo. Provide --repo or set GITHUB_DEFAULT_REPO.")
    return repo

