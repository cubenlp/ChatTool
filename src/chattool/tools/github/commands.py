from __future__ import annotations

import time
from typing import Optional

import click

from chattool.tools.github.api import (
    configure_github_https_token,
    get_client,
    resolve_repo,
    resolve_repo_from_git_remote,
    resolve_token,
    save_github_token_to_env,
)
from chattool.tools.github.render import (
    collect_merge_blockers,
    derive_repo_capabilities,
    has_incomplete_pr_checks,
    tail_text,
)
from chattool.tools.github.requests import (
    get_job_logs,
    get_pr_checks,
    get_pr_list,
    get_pr_view,
    get_repo_permissions,
    get_run_view,
    patch_pr_edit,
    post_pr_comment,
    post_pr_create,
    post_pr_merge,
)


def resolve_repo_and_credential_path(repo: Optional[str]) -> tuple[str, str]:
    if repo:
        normalized = resolve_repo(repo)
        return normalized, f"{normalized}.git"
    return resolve_repo_from_git_remote()


def create_pr(
    repo: Optional[str],
    base: str,
    head: str,
    title: str,
    body: str,
    token: Optional[str],
) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, require_token=True, credential_path=credential_path)
    return post_pr_create(client, resolved_repo, base, head, title, body)


def list_prs(
    repo: Optional[str],
    state: str,
    limit: int,
    token: Optional[str],
) -> list[dict]:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, credential_path=credential_path)
    return get_pr_list(client, resolved_repo, state, limit)


def view_pr(repo: Optional[str], number: int, token: Optional[str]) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, credential_path=credential_path)
    return get_pr_view(client, resolved_repo, number)


def check_pr(
    repo: Optional[str],
    number: int,
    check_limit: int,
    workflow_limit: int,
    wait_for_completion: bool,
    interval: float,
    timeout: Optional[float],
    token: Optional[str],
) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, credential_path=credential_path)
    started_at = time.monotonic()
    while True:
        payload = get_pr_checks(
            client,
            resolved_repo,
            number,
            check_limit=check_limit,
            workflow_limit=workflow_limit,
        )
        if not wait_for_completion or not has_incomplete_pr_checks(payload):
            return payload
        if timeout is not None and (time.monotonic() - started_at) >= timeout:
            raise click.ClickException(
                f"Timed out after {timeout:g}s waiting for PR #{number} checks to finish."
            )
        click.echo(
            f"Waiting for PR #{number} checks to finish; polling again in {interval:g}s...",
            err=True,
        )
        time.sleep(interval)


def comment_pr(repo: Optional[str], number: int, body: str, token: Optional[str]) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, require_token=True, credential_path=credential_path)
    return post_pr_comment(client, resolved_repo, number, body)


def merge_pr(
    repo: Optional[str],
    number: int,
    method: str,
    title: Optional[str],
    message: Optional[str],
    check_before_merge: bool,
    token: Optional[str],
) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, require_token=True, credential_path=credential_path)
    if check_before_merge:
        payload = get_pr_checks(
            client,
            resolved_repo,
            number,
            check_limit=20,
            workflow_limit=10,
        )
        blockers = collect_merge_blockers(payload)
        if blockers:
            details = "\n".join(f"- {item}" for item in blockers)
            raise click.ClickException(
                "Refusing to merge because CI checks are not green:\n"
                f"{details}\n"
                f"Run `chattool gh pr checks --number {number}` for details, "
                "or rerun without `--check` if you intentionally want to merge anyway."
            )
    result = post_pr_merge(client, resolved_repo, number, method, title, message)
    if not result["merged"]:
        raise click.ClickException(f"Merge failed: {result['message']}")
    return result


def edit_pr(
    repo: Optional[str],
    number: int,
    title: Optional[str],
    body: Optional[str],
    state: Optional[str],
    base: Optional[str],
    token: Optional[str],
) -> dict:
    if title is None and body is None and state is None and base is None:
        raise click.ClickException("No updates provided. Use --title/--body/--state/--base.")
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    client = get_client(token, require_token=True, credential_path=credential_path)
    return patch_pr_edit(
        client,
        resolved_repo,
        number,
        title=title,
        body=body,
        state=state,
        base=base,
    )


def view_run(
    repo: Optional[str],
    run_id: int,
    job_limit: int,
    token: Optional[str],
) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    resolved_token = resolve_token(token, credential_path=credential_path)
    return get_run_view(resolved_repo, run_id, resolved_token, job_limit)


def view_job_logs(
    repo: Optional[str],
    job_id: int,
    tail: int,
    output: Optional[str],
    token: Optional[str],
) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    resolved_token = resolve_token(token, credential_path=credential_path)
    payload = get_job_logs(resolved_repo, job_id, resolved_token)
    rendered_log = tail_text(payload["log"], tail)
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(payload["log"])
    return {
        "job": payload["job"],
        "tail": tail,
        "output_path": output,
        "log": payload["log"],
        "rendered_log": rendered_log,
    }


def repo_perms(repo: Optional[str], full_json: bool, token: Optional[str]) -> dict:
    resolved_repo, credential_path = resolve_repo_and_credential_path(repo)
    resolved_token = resolve_token(token, credential_path=credential_path)
    payload = get_repo_permissions(resolved_repo, resolved_token)
    permissions = payload.get("permissions") or {}
    result = {
        "repo": payload.get("full_name") or resolved_repo,
        "private": payload.get("private"),
        "visibility": payload.get("visibility"),
        "permissions": permissions,
        "capabilities": derive_repo_capabilities(permissions),
    }
    if full_json:
        result["repository"] = payload
    return result


def set_token(token: Optional[str], save_env: bool) -> dict:
    repo, credential_path = resolve_repo_from_git_remote()
    resolved_token = resolve_token(
        token,
        credential_path=credential_path,
        exact_only=True,
    ) or resolve_token(token, credential_path=credential_path)
    if not resolved_token:
        raise click.ClickException(
            "Missing token. Provide --token or configure a GitHub credential for the current repository."
        )
    configure_github_https_token(credential_path, resolved_token)
    if save_env:
        save_github_token_to_env(resolved_token)
    return {"repo": repo, "saved_env": save_env}
