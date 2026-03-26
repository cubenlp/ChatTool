import json
import time
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
        "mergeable": getattr(pr, "mergeable", None),
        "mergeable_state": getattr(pr, "mergeable_state", None),
    }

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"#{payload['number']} [{payload['state']}] {payload['title']}")
    click.echo(f"Author: {payload['author']}")
    click.echo(f"URL: {payload['url']}")
    click.echo(f"Base: {payload['base']}  Head: {payload['head']}")
    click.echo(
        f"Mergeable: {_format_optional(payload['mergeable'])}  "
        f"Merge State: {_format_optional(payload['mergeable_state'])}"
    )
    click.echo(f"Created: {payload['created_at']}  Updated: {payload['updated_at']}")
    click.echo(f"Merged: {payload['merged_at']}")


@cli.command(name="pr-check")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--number", required=True, type=int, help="Pull request number.")
@click.option("--check-limit", default=20, type=int, show_default=True, help="Max check runs to show.")
@click.option("--workflow-limit", default=10, type=int, show_default=True, help="Max workflow runs to show.")
@click.option("--wait", "wait_for_completion", is_flag=True, help="Wait until checks and workflow runs finish.")
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
    help="Optional max wait time in seconds. By default, wait forever.",
)
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_check(repo, number, check_limit, workflow_limit, wait_for_completion, interval, timeout, json_output, token):
    """Show CI/check status for a pull request."""
    from github.GithubException import GithubException

    client = _get_client(token)
    repo = _resolve_repo(repo)
    try:
        repo_obj = client.get_repo(repo)
        started_at = time.monotonic()
        while True:
            pr = repo_obj.get_pull(number)
            commit = repo_obj.get_commit(pr.head.sha)
            payload = _build_pr_check_payload(
                pr,
                commit,
                repo_obj,
                check_limit=check_limit,
                workflow_limit=workflow_limit,
            )
            if not wait_for_completion or not _has_incomplete_pr_checks(payload):
                break
            if timeout is not None and (time.monotonic() - started_at) >= timeout:
                raise click.ClickException(
                    f"Timed out after {timeout:g}s waiting for PR #{number} checks to finish."
                )
            click.echo(
                f"Waiting for PR #{number} checks to finish; polling again in {interval:g}s...",
                err=True,
            )
            time.sleep(interval)
    except GithubException as exc:
        raise click.ClickException(f"GitHub API error: {exc}") from exc

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    _echo_pr_check_payload(payload)


@cli.command(name="run-view")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--run-id", required=True, type=int, help="Workflow run id.")
@click.option("--job-limit", default=50, type=int, show_default=True, help="Max jobs to show.")
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def run_view(repo, run_id, job_limit, json_output, token):
    """Show a workflow run and its jobs."""
    repo = _resolve_repo(repo)
    token = _resolve_token(token)

    run_payload = _github_api_get_json(repo, f"/actions/runs/{run_id}", token)
    jobs_payload = _github_api_get_json(
        repo,
        f"/actions/runs/{run_id}/jobs",
        token,
        params={"per_page": min(max(job_limit, 1), 100)},
    )
    payload = _build_workflow_run_payload(run_payload, jobs_payload, job_limit=job_limit)

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    _echo_workflow_run_payload(payload)


@cli.command(name="job-logs")
@click.option("--repo", required=False, help="Repository in owner/name form (or set GITHUB_DEFAULT_REPO).")
@click.option("--job-id", required=True, type=int, help="Workflow job id.")
@click.option(
    "--tail",
    default=200,
    type=click.IntRange(min=0),
    show_default=True,
    help="Show only the last N lines. Use 0 to print the full log.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write the full log to a local file.",
)
@click.option("--json-output", is_flag=True, help="Output JSON.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def job_logs(repo, job_id, tail, output, json_output, token):
    """Show logs for a workflow job."""
    repo = _resolve_repo(repo)
    token = _resolve_token(token)

    job_payload = _github_api_get_json(repo, f"/actions/jobs/{job_id}", token)
    logs_text = _github_api_get_text(repo, f"/actions/jobs/{job_id}/logs", token)
    rendered_log = _tail_text(logs_text, tail)

    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(logs_text)

    payload = {
        "job": _build_workflow_job_payload(job_payload),
        "tail": tail,
        "output_path": output,
        "log": logs_text if json_output else rendered_log,
    }

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    _echo_workflow_job_payload(payload["job"])
    if output:
        click.echo(f"Saved full log to: {output}")
    click.echo("Log:")
    click.echo(rendered_log)


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
@click.option("--check", "check_before_merge", is_flag=True, help="Check CI status before merging and abort if checks are not green.")
@click.option("--token", default=None, help="GitHub token (or set GITHUB_ACCESS_TOKEN).")
def pr_merge(repo, number, method, title, message, confirm, check_before_merge, token):
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
        if check_before_merge:
            commit = repo_obj.get_commit(pr.head.sha)
            check_payload = _build_pr_check_payload(
                pr,
                commit,
                repo_obj,
                check_limit=20,
                workflow_limit=10,
            )
            blockers = _collect_merge_blockers(check_payload)
            if blockers:
                details = "\n".join(f"- {item}" for item in blockers)
                raise click.ClickException(
                    "Refusing to merge because CI checks are not green:\n"
                    f"{details}\n"
                    f"Run `chattool gh pr-check --number {number}` for details, "
                    "or rerun without `--check` if you intentionally want to merge anyway."
                )
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

    token = _resolve_token(token)
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


def _resolve_token(token: Optional[str]) -> Optional[str]:
    return token or GitHubConfig.GITHUB_ACCESS_TOKEN.value


def _build_pr_check_payload(pr, commit, repo_obj, check_limit: int, workflow_limit: int) -> dict:
    combined_status = commit.get_combined_status()
    statuses = []
    for status in combined_status.statuses:
        statuses.append({
            "context": status.context,
            "state": status.state,
            "description": status.description,
            "target_url": status.target_url,
            "updated_at": _isoformat(status.updated_at),
        })

    check_runs = []
    for check_run in commit.get_check_runs():
        check_runs.append({
            "name": check_run.name,
            "status": check_run.status,
            "conclusion": check_run.conclusion,
            "details_url": check_run.details_url,
            "html_url": getattr(check_run, "html_url", None),
            "app": check_run.app.name if getattr(check_run, "app", None) else None,
            "started_at": _isoformat(check_run.started_at),
            "completed_at": _isoformat(check_run.completed_at),
        })
        if len(check_runs) >= check_limit:
            break

    workflow_runs = []
    for workflow_run in repo_obj.get_workflow_runs(head_sha=pr.head.sha):
        workflow_runs.append({
            "name": workflow_run.name,
            "display_title": workflow_run.display_title,
            "event": workflow_run.event,
            "status": workflow_run.status,
            "conclusion": workflow_run.conclusion,
            "html_url": workflow_run.html_url,
            "created_at": _isoformat(workflow_run.created_at),
            "updated_at": _isoformat(workflow_run.updated_at),
            "run_started_at": _isoformat(getattr(workflow_run, "run_started_at", None)),
            "head_branch": workflow_run.head_branch,
            "head_sha": workflow_run.head_sha,
            "run_number": workflow_run.run_number,
        })
        if len(workflow_runs) >= workflow_limit:
            break

    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "url": pr.html_url,
        "author": pr.user.login if pr.user else None,
        "base": pr.base.ref if pr.base else None,
        "head": pr.head.ref if pr.head else None,
        "head_sha": pr.head.sha if pr.head else None,
        "mergeable": getattr(pr, "mergeable", None),
        "mergeable_state": getattr(pr, "mergeable_state", None),
        "combined_status": {
            "state": combined_status.state,
            "sha": combined_status.sha,
            "total_count": combined_status.total_count,
            "statuses": statuses,
        },
        "check_runs": check_runs,
        "workflow_runs": workflow_runs,
    }


def _build_workflow_run_payload(run_payload: dict, jobs_payload: dict, job_limit: int) -> dict:
    jobs = [
        _build_workflow_job_payload(job_payload)
        for job_payload in jobs_payload.get("jobs", [])[:job_limit]
    ]
    return {
        "id": run_payload["id"],
        "name": run_payload.get("name"),
        "display_title": run_payload.get("display_title"),
        "event": run_payload.get("event"),
        "status": run_payload.get("status"),
        "conclusion": run_payload.get("conclusion"),
        "html_url": run_payload.get("html_url"),
        "created_at": run_payload.get("created_at"),
        "updated_at": run_payload.get("updated_at"),
        "run_started_at": run_payload.get("run_started_at"),
        "head_branch": run_payload.get("head_branch"),
        "head_sha": run_payload.get("head_sha"),
        "run_number": run_payload.get("run_number"),
        "jobs": jobs,
        "jobs_total_count": jobs_payload.get("total_count", len(jobs)),
    }


def _build_workflow_job_payload(job_payload: dict) -> dict:
    return {
        "id": job_payload["id"],
        "name": job_payload.get("name"),
        "status": job_payload.get("status"),
        "conclusion": job_payload.get("conclusion"),
        "html_url": job_payload.get("html_url"),
        "runner_name": job_payload.get("runner_name"),
        "runner_group_name": job_payload.get("runner_group_name"),
        "labels": job_payload.get("labels") or [],
        "started_at": job_payload.get("started_at"),
        "completed_at": job_payload.get("completed_at"),
        "steps": [
            {
                "number": step.get("number"),
                "name": step.get("name"),
                "status": step.get("status"),
                "conclusion": step.get("conclusion"),
            }
            for step in job_payload.get("steps", [])
        ],
    }


def _echo_pr_check_payload(payload: dict) -> None:
    click.echo(f"#{payload['number']} [{payload['state']}] {payload['title']}")
    click.echo(f"Author: {payload['author']}")
    click.echo(f"URL: {payload['url']}")
    click.echo(f"Base: {payload['base']}  Head: {payload['head']}")
    click.echo(f"Head SHA: {payload['head_sha']}")
    click.echo(
        f"Mergeable: {_format_optional(payload['mergeable'])}  "
        f"Merge State: {_format_optional(payload['mergeable_state'])}"
    )

    combined = payload["combined_status"]
    click.echo(
        f"Combined status: {combined['state']} "
        f"({combined['total_count']} status{'es' if combined['total_count'] != 1 else ''})"
    )

    if combined["statuses"]:
        click.echo("Statuses:")
        for status in combined["statuses"]:
            desc = f" - {status['description']}" if status["description"] else ""
            click.echo(f"  - {status['context']}: {status['state']}{desc}")
            if status["target_url"]:
                click.echo(f"    {status['target_url']}")
    else:
        click.echo("Statuses: none")

    if payload["check_runs"]:
        click.echo("Check runs:")
        for check_run in payload["check_runs"]:
            conclusion = check_run["conclusion"] or "-"
            app = f" [{check_run['app']}]" if check_run["app"] else ""
            click.echo(f"  - {check_run['name']}: {check_run['status']}/{conclusion}{app}")
            if check_run["details_url"]:
                click.echo(f"    {check_run['details_url']}")
    else:
        click.echo("Check runs: none")

    if payload["workflow_runs"]:
        click.echo("Workflow runs:")
        for workflow_run in payload["workflow_runs"]:
            conclusion = workflow_run["conclusion"] or "-"
            click.echo(
                f"  - {workflow_run['name']}: {workflow_run['status']}/{conclusion} "
                f"(event={workflow_run['event']}, run={workflow_run['run_number']})"
            )
            if workflow_run["html_url"]:
                click.echo(f"    {workflow_run['html_url']}")
    else:
        click.echo("Workflow runs: none")


def _echo_workflow_run_payload(payload: dict) -> None:
    conclusion = payload["conclusion"] or "-"
    click.echo(
        f"Run #{payload['run_number']} (id={payload['id']}): "
        f"{payload['status']}/{conclusion}"
    )
    click.echo(f"Name: {payload['name']}")
    click.echo(f"Title: {payload['display_title']}")
    click.echo(f"Event: {payload['event']}")
    click.echo(f"URL: {payload['html_url']}")
    click.echo(f"Branch: {payload['head_branch']}")
    click.echo(f"Head SHA: {payload['head_sha']}")

    if payload["jobs"]:
        click.echo(f"Jobs ({len(payload['jobs'])}/{payload['jobs_total_count']} shown):")
        for job in payload["jobs"]:
            _echo_workflow_job_payload(job, prefix="  - ")
    else:
        click.echo("Jobs: none")


def _echo_workflow_job_payload(payload: dict, prefix: str = "") -> None:
    conclusion = payload["conclusion"] or "-"
    click.echo(f"{prefix}{payload['name']} (id={payload['id']}): {payload['status']}/{conclusion}")
    if payload["html_url"]:
        click.echo(f"{prefix}  {payload['html_url']}")
    runner_bits = [bit for bit in [payload["runner_name"], payload["runner_group_name"]] if bit]
    if runner_bits:
        click.echo(f"{prefix}  runner: {' / '.join(runner_bits)}")
    if payload["labels"]:
        click.echo(f"{prefix}  labels: {', '.join(payload['labels'])}")
    if payload["steps"]:
        click.echo(f"{prefix}  steps:")
        for step in payload["steps"]:
            step_conclusion = step["conclusion"] or "-"
            click.echo(f"{prefix}    - [{step['number']}] {step['name']}: {step['status']}/{step_conclusion}")


def _collect_merge_blockers(payload: dict) -> list[str]:
    blockers: list[str] = []

    for status in payload["combined_status"]["statuses"]:
        if status["state"] != "success":
            blockers.append(f"status {status['context']} is {status['state']}")

    for check_run in payload["check_runs"]:
        status = check_run["status"]
        conclusion = check_run["conclusion"]
        if status != "completed":
            blockers.append(f"check run {check_run['name']} is {status}")
            continue
        if conclusion not in {"success", "neutral", "skipped"}:
            blockers.append(f"check run {check_run['name']} concluded {conclusion or 'unknown'}")

    for workflow_run in payload["workflow_runs"]:
        status = workflow_run["status"]
        conclusion = workflow_run["conclusion"]
        if status != "completed":
            blockers.append(f"workflow {workflow_run['name']} is {status}")
            continue
        if conclusion not in {"success", "neutral", "skipped"}:
            blockers.append(f"workflow {workflow_run['name']} concluded {conclusion or 'unknown'}")

    return blockers


def _has_incomplete_pr_checks(payload: dict) -> bool:
    for status in payload["combined_status"]["statuses"]:
        if status["state"] in {"pending"}:
            return True

    for check_run in payload["check_runs"]:
        if check_run["status"] != "completed":
            return True

    for workflow_run in payload["workflow_runs"]:
        if workflow_run["status"] != "completed":
            return True

    return False


def _isoformat(value) -> Optional[str]:
    return value.isoformat() if value else None


def _format_optional(value) -> str:
    return "-" if value is None else str(value)


def _github_api_get_json(repo: str, path: str, token: Optional[str], params: Optional[dict] = None) -> dict:
    response = _github_api_request(repo, path, token, params=params)
    try:
        return response.json()
    except ValueError as exc:
        raise click.ClickException(f"GitHub API returned non-JSON response for {path}") from exc


def _github_api_get_text(repo: str, path: str, token: Optional[str], params: Optional[dict] = None) -> str:
    response = _github_api_request(repo, path, token, params=params)
    return response.text


def _github_api_request(repo: str, path: str, token: Optional[str], params: Optional[dict] = None):
    import requests

    owner, name = _split_repo(repo)
    url = f"https://api.github.com/repos/{owner}/{name}{path}"
    try:
        response = requests.get(
            url,
            headers=_github_api_headers(token),
            params=params,
            timeout=30,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise click.ClickException(f"GitHub API request failed for {path}: {exc}") from exc
    if response.ok:
        return response

    detail = response.text.strip()
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("message"):
            detail = payload["message"]
    except ValueError:
        pass
    raise click.ClickException(f"GitHub API error ({response.status_code}) for {path}: {detail}")


def _github_api_headers(token: Optional[str]) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "chattool-gh",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _split_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise click.ClickException("Repo must be in owner/name form.")
    return parts[0], parts[1]


def _tail_text(text: str, tail: int) -> str:
    if tail == 0:
        return text
    lines = text.splitlines()
    if len(lines) <= tail:
        return text
    return "\n".join(lines[-tail:])
