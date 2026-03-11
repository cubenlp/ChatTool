import os
import click


@click.group(name="gh")
def cli():
    """GitHub helpers (PR, issues)."""
    pass


@cli.command(name="pr-create")
@click.option("--repo", required=True, help="Repository in owner/name form.")
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

    token = token or os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise click.ClickException("Missing token. Set GITHUB_ACCESS_TOKEN or pass --token.")

    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            body = handle.read()

    client = Github(token)
    try:
        repo_obj = client.get_repo(repo)
        pr = repo_obj.create_pull(title=title, body=body, base=base, head=head)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    click.echo(f"PR created: {pr.html_url}")
