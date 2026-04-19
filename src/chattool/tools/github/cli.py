import json

import click

from chattool.interaction import (
    BACK_VALUE,
    CommandField,
    CommandSchema,
    add_interactive_option,
    ask_text,
    is_interactive_available,
    resolve_command_inputs,
)
from chattool.utils import mask_secret
from chattool.tools.github.api import resolve_token
from chattool.tools.github.commands import (
    check_pr,
    comment_pr,
    create_pr,
    edit_pr,
    merge_pr,
    repo_perms,
    resolve_repo_and_credential_path,
    set_token,
    view_job_logs,
    view_pr,
    view_run,
    list_prs,
)
from chattool.tools.github.render import (
    echo_pr_checks,
    echo_pr_list,
    echo_pr_view,
    echo_workflow_job,
    echo_workflow_run,
    format_optional,
)


PR_CREATE_SCHEMA = CommandSchema(
    name="gh-pr-create",
    fields=(
        CommandField("base", prompt="base", required=True),
        CommandField("head", prompt="head", required=True),
        CommandField("title", prompt="title", required=True),
    ),
)


PR_NUMBER_SCHEMA = CommandSchema(
    name="gh-pr-number",
    fields=(CommandField("number", prompt="pr number", kind="int", required=True),),
)


RUN_ID_SCHEMA = CommandSchema(
    name="gh-run-id",
    fields=(CommandField("run_id", prompt="workflow run id", kind="int", required=True),),
)


JOB_ID_SCHEMA = CommandSchema(
    name="gh-job-id",
    fields=(CommandField("job_id", prompt="workflow job id", kind="int", required=True),),
)


PR_COMMENT_SCHEMA = CommandSchema(
    name="gh-pr-comment",
    fields=(
        CommandField("number", prompt="pr number", kind="int", required=True),
        CommandField("body", prompt="comment body", required=True),
    ),
)


@click.group(name="gh")
def cli():
    """GitHub helpers (PR, actions)."""


@cli.group(name="pr")
def pr_group():
    """Pull request helpers."""


@cli.group(name="run")
def run_group():
    """GitHub Actions helpers."""


@pr_group.command(name="create")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--base", required=False, help="Base branch (e.g., main).")
@click.option("--head", required=False, help="Head branch or owner:branch.")
@click.option("--title", required=False, help="Pull request title.")
@click.option("--body", default="", help="Pull request body.")
@click.option(
    "--body-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Read PR body from file (overrides --body).",
)
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_create(repo, base, head, title, body, body_file, token, interactive):
    """Create a GitHub pull request."""
    inputs = resolve_command_inputs(
        schema=PR_CREATE_SCHEMA,
        provided={"base": base, "head": head, "title": title},
        interactive=interactive,
        usage="Usage: chattool gh pr create [--repo TEXT] --base TEXT --head TEXT --title TEXT [-i|-I]",
    )
    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            body = handle.read()
    payload = create_pr(
        repo,
        inputs["base"],
        inputs["head"],
        inputs["title"],
        body,
        token,
    )
    click.echo(f"PR created: {payload['url']}")


@pr_group.command(name="list")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option(
    "--state",
    default="open",
    type=click.Choice(["open", "closed", "all"]),
    show_default=True,
)
@click.option("--limit", default=20, type=int, show_default=True, help="Max PRs to show.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token.")
def pr_list(repo, state, limit, json_output, token):
    """List pull requests."""
    items = list_prs(repo, state, limit, token)
    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return
    echo_pr_list(items)


@pr_group.command(name="view")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--number", required=False, type=int, help="Pull request number.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_view(repo, number, json_output, token, interactive):
    """Show pull request details."""
    inputs = resolve_command_inputs(
        schema=PR_NUMBER_SCHEMA,
        provided={"number": number},
        interactive=interactive,
        usage="Usage: chattool gh pr view [--repo TEXT] --number INTEGER [-i|-I]",
    )
    payload = view_pr(repo, inputs["number"], token)
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    echo_pr_view(payload)


@pr_group.command(name="checks")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--number", required=False, type=int, help="Pull request number.")
@click.option(
    "--check-limit",
    default=20,
    type=int,
    show_default=True,
    help="Max check runs to show.",
)
@click.option(
    "--workflow-limit",
    default=10,
    type=int,
    show_default=True,
    help="Max workflow runs to show.",
)
@click.option(
    "--wait",
    "wait_for_completion",
    is_flag=True,
    help="Wait until checks and workflow runs finish.",
)
@click.option(
    "--interval",
    default=15,
    type=click.FloatRange(min=1e-9),
    show_default=True,
    help="Polling interval in seconds when --wait is used.",
)
@click.option(
    "--timeout",
    default=None,
    type=click.FloatRange(min=1e-9),
    help="Optional max wait time in seconds.",
)
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_checks(
    repo,
    number,
    check_limit,
    workflow_limit,
    wait_for_completion,
    interval,
    timeout,
    json_output,
    token,
    interactive,
):
    """Show CI/check status for a pull request."""
    inputs = resolve_command_inputs(
        schema=PR_NUMBER_SCHEMA,
        provided={"number": number},
        interactive=interactive,
        usage="Usage: chattool gh pr checks [--repo TEXT] --number INTEGER [-i|-I]",
    )
    payload = check_pr(
        repo,
        inputs["number"],
        check_limit,
        workflow_limit,
        wait_for_completion,
        interval,
        timeout,
        token,
    )
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    echo_pr_checks(payload)


@pr_group.command(name="comment")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--number", required=False, type=int, help="Pull request number.")
@click.option("--body", required=False, help="Comment body.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_comment(repo, number, body, token, interactive):
    """Add a comment to a pull request."""
    inputs = resolve_command_inputs(
        schema=PR_COMMENT_SCHEMA,
        provided={"number": number, "body": body},
        interactive=interactive,
        usage="Usage: chattool gh pr comment [--repo TEXT] --number INTEGER --body TEXT [-i|-I]",
    )
    payload = comment_pr(repo, inputs["number"], inputs["body"], token)
    click.echo(f"Comment created: {payload['url']}")


@pr_group.command(name="merge")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--number", required=False, type=int, help="Pull request number.")
@click.option(
    "--method",
    default="merge",
    type=click.Choice(["merge", "squash", "rebase"]),
    show_default=True,
)
@click.option("--title", default=None, help="Optional merge title.")
@click.option("--message", default=None, help="Optional merge message.")
@click.option(
    "--check",
    "check_before_merge",
    is_flag=True,
    help="Check CI status before merging and abort if checks are not green.",
)
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_merge(repo, number, method, title, message, check_before_merge, token, interactive):
    """Merge a pull request."""
    inputs = resolve_command_inputs(
        schema=PR_NUMBER_SCHEMA,
        provided={"number": number},
        interactive=interactive,
        usage="Usage: chattool gh pr merge [--repo TEXT] --number INTEGER [-i|-I]",
    )
    payload = merge_pr(
        repo,
        inputs["number"],
        method,
        title,
        message,
        check_before_merge,
        token,
    )
    click.echo(f"PR merged: {payload['url']}")


@pr_group.command(name="edit")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--number", required=False, type=int, help="Pull request number.")
@click.option("--title", default=None, help="New pull request title.")
@click.option("--body", default=None, help="New pull request body.")
@click.option(
    "--body-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Read PR body from file (overrides --body).",
)
@click.option("--state", default=None, type=click.Choice(["open", "closed"]))
@click.option("--base", default=None, help="Change base branch.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def pr_edit(repo, number, title, body, body_file, state, base, token, interactive):
    """Update pull request metadata."""
    inputs = resolve_command_inputs(
        schema=PR_NUMBER_SCHEMA,
        provided={"number": number},
        interactive=interactive,
        usage="Usage: chattool gh pr edit [--repo TEXT] --number INTEGER [-i|-I]",
    )
    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            body = handle.read()
    payload = edit_pr(repo, inputs["number"], title, body, state, base, token)
    click.echo(f"PR updated: {payload['url']}")


@run_group.command(name="view")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--run-id", required=False, type=int, help="Workflow run id.")
@click.option("--job-limit", default=50, type=int, show_default=True, help="Max jobs to show.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def run_view(repo, run_id, job_limit, json_output, token, interactive):
    """Show a workflow run and its jobs."""
    inputs = resolve_command_inputs(
        schema=RUN_ID_SCHEMA,
        provided={"run_id": run_id},
        interactive=interactive,
        usage="Usage: chattool gh run view [--repo TEXT] --run-id INTEGER [-i|-I]",
    )
    payload = view_run(repo, inputs["run_id"], job_limit, token)
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    echo_workflow_run(payload)


@run_group.command(name="logs")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--job-id", required=False, type=int, help="Workflow job id.")
@click.option(
    "--tail",
    default=200,
    type=click.IntRange(min=0),
    show_default=True,
    help="Show only the last N lines. Use 0 for the full log.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write the full log to a local file.",
)
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token.")
@add_interactive_option
def run_logs(repo, job_id, tail, output, json_output, token, interactive):
    """Show logs for a workflow job."""
    inputs = resolve_command_inputs(
        schema=JOB_ID_SCHEMA,
        provided={"job_id": job_id},
        interactive=interactive,
        usage="Usage: chattool gh run logs [--repo TEXT] --job-id INTEGER [-i|-I]",
    )
    payload = view_job_logs(repo, inputs["job_id"], tail, output, token)
    if json_output:
        click.echo(
            json.dumps(
                {
                    "job": payload["job"],
                    "tail": payload["tail"],
                    "output_path": payload["output_path"],
                    "log": payload["log"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    echo_workflow_job(payload["job"])
    if output:
        click.echo(f"Saved full log to: {output}")
    click.echo("Log:")
    click.echo(payload["rendered_log"])


@cli.command(name="repo-perms")
@click.option("--repo", required=False, help="Repository in owner/name form.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--full-json", is_flag=True, help="Include the full repository payload.")
@click.option("--token", default=None, help="GitHub token.")
def repo_permissions(repo, json_output, full_json, token):
    """Show repository permissions for the current token."""
    payload = repo_perms(repo, full_json, token)
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"Repo: {payload['repo']}")
    click.echo(f"Private: {format_optional(payload['private'])}")
    click.echo(f"Visibility: {format_optional(payload['visibility'])}")
    click.echo("Permissions:")
    if not payload["permissions"]:
        click.echo("  - none returned")
    else:
        for key in sorted(payload["permissions"]):
            click.echo(f"  - {key}: {payload['permissions'][key]}")
    click.echo("Capabilities:")
    for key, value in payload["capabilities"].items():
        click.echo(f"  - {key}: {value}")


@cli.command(name="set-token")
@click.option("--token", default=None, help="GitHub token.")
@click.option("--save-env", is_flag=True, help="Also save the token into ChatTool env config.")
def set_repo_token(token, save_env):
    """Configure HTTPS credentials for the current GitHub repository."""
    repo, credential_path = resolve_repo_and_credential_path(None)
    resolved_token = resolve_token(token, credential_path=credential_path, exact_only=True)
    if resolved_token is None:
        resolved_token = resolve_token(token, credential_path=credential_path)
    if is_interactive_available():
        prompt_label = "github_token"
        if resolved_token:
            prompt_label += f" (current: {mask_secret(resolved_token)}, enter to keep)"
        token_input = ask_text(prompt_label, password=True)
        if token_input == BACK_VALUE:
            raise click.Abort()
        entered = str(token_input).strip()
        if entered:
            resolved_token = entered
    result = set_token(resolved_token, save_env)
    click.echo(f"Configured Git HTTPS token for {result['repo']}.")
    if result["saved_env"]:
        click.echo("Saved token to ChatTool GitHub env config.")
