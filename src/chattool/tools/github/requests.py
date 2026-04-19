from __future__ import annotations

from typing import Optional

from chattool.tools.github.api import github_api_get_json, github_api_get_text


def get_pr_list(client, repo: str, state: str, limit: int) -> list[dict]:
    repo_obj = client.get_repo(repo)
    items: list[dict] = []
    for pr in repo_obj.get_pulls(state=state, sort="updated", direction="desc"):
        items.append(_build_pr_view_payload(pr))
        if len(items) >= limit:
            break
    return items


def get_pr_view(client, repo: str, number: int) -> dict:
    repo_obj = client.get_repo(repo)
    pr = repo_obj.get_pull(number)
    return _build_pr_view_payload(pr)


def get_pr_checks(
    client,
    repo: str,
    number: int,
    check_limit: int,
    workflow_limit: int,
) -> dict:
    repo_obj = client.get_repo(repo)
    pr = repo_obj.get_pull(number)
    commit = repo_obj.get_commit(pr.head.sha)
    return _build_pr_check_payload(
        pr,
        commit,
        repo_obj,
        check_limit=check_limit,
        workflow_limit=workflow_limit,
    )


def post_pr_create(client, repo: str, base: str, head: str, title: str, body: str) -> dict:
    repo_obj = client.get_repo(repo)
    pr = repo_obj.create_pull(title=title, body=body, base=base, head=head)
    return _build_pr_view_payload(pr)


def post_pr_comment(client, repo: str, number: int, body: str) -> dict:
    repo_obj = client.get_repo(repo)
    pr = repo_obj.get_pull(number)
    comment = pr.create_issue_comment(body)
    return {
        "url": comment.html_url,
        "body": comment.body,
        "id": getattr(comment, "id", None),
    }


def post_pr_merge(
    client,
    repo: str,
    number: int,
    method: str,
    title: Optional[str],
    message: Optional[str],
) -> dict:
    repo_obj = client.get_repo(repo)
    pr = repo_obj.get_pull(number)
    payload = {"merge_method": method}
    if title is not None:
        payload["commit_title"] = title
    if message is not None:
        payload["commit_message"] = message
    result = pr.merge(**payload)
    return {
        "merged": result.merged,
        "message": result.message,
        "url": pr.html_url,
    }


def patch_pr_edit(
    client,
    repo: str,
    number: int,
    *,
    title: Optional[str],
    body: Optional[str],
    state: Optional[str],
    base: Optional[str],
) -> dict:
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
    return _build_pr_view_payload(pr)


def get_repo_permissions(repo: str, token: Optional[str]) -> dict:
    return github_api_get_json(repo, "", token)


def get_run_view(repo: str, run_id: int, token: Optional[str], job_limit: int) -> dict:
    run_payload = github_api_get_json(repo, f"/actions/runs/{run_id}", token)
    jobs_payload = github_api_get_json(
        repo,
        f"/actions/runs/{run_id}/jobs",
        token,
        params={"per_page": min(max(job_limit, 1), 100)},
    )
    return _build_workflow_run_payload(run_payload, jobs_payload, job_limit=job_limit)


def get_job_logs(repo: str, job_id: int, token: Optional[str]) -> dict:
    job_payload = github_api_get_json(repo, f"/actions/jobs/{job_id}", token)
    logs_text = github_api_get_text(repo, f"/actions/jobs/{job_id}/logs", token)
    return {
        "job": _build_workflow_job_payload(job_payload),
        "log": logs_text,
    }


def _build_pr_view_payload(pr) -> dict:
    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "url": pr.html_url,
        "author": pr.user.login if pr.user else None,
        "created_at": _isoformat(getattr(pr, "created_at", None)),
        "updated_at": _isoformat(getattr(pr, "updated_at", None)),
        "merged_at": _isoformat(getattr(pr, "merged_at", None)),
        "base": pr.base.ref if pr.base else None,
        "head": pr.head.ref if pr.head else None,
        "head_sha": pr.head.sha if pr.head else None,
        "mergeable": getattr(pr, "mergeable", None),
        "mergeable_state": getattr(pr, "mergeable_state", None),
    }


def _build_pr_check_payload(
    pr,
    commit,
    repo_obj,
    check_limit: int,
    workflow_limit: int,
) -> dict:
    payload = _build_pr_view_payload(pr)
    statuses = []
    try:
        combined_status = commit.get_combined_status()
        for status in combined_status.statuses:
            statuses.append(
                {
                    "context": status.context,
                    "state": status.state,
                    "description": status.description,
                    "target_url": status.target_url,
                    "updated_at": _isoformat(status.updated_at),
                }
            )
        combined_status_payload = {
            "state": combined_status.state,
            "sha": combined_status.sha,
            "total_count": combined_status.total_count,
            "statuses": statuses,
        }
    except Exception as exc:
        combined_status_payload = {
            "state": "unavailable",
            "sha": getattr(pr.head, "sha", None),
            "total_count": 0,
            "statuses": [],
            "error": str(exc),
        }

    check_runs = []
    for check_run in commit.get_check_runs():
        check_runs.append(
            {
                "name": check_run.name,
                "status": check_run.status,
                "conclusion": check_run.conclusion,
                "details_url": check_run.details_url,
                "html_url": getattr(check_run, "html_url", None),
                "app": check_run.app.name if getattr(check_run, "app", None) else None,
                "started_at": _isoformat(check_run.started_at),
                "completed_at": _isoformat(check_run.completed_at),
            }
        )
        if len(check_runs) >= check_limit:
            break

    workflow_runs = []
    for workflow_run in repo_obj.get_workflow_runs(head_sha=pr.head.sha):
        workflow_runs.append(
            {
                "name": workflow_run.name,
                "display_title": workflow_run.display_title,
                "event": workflow_run.event,
                "status": workflow_run.status,
                "conclusion": workflow_run.conclusion,
                "html_url": workflow_run.html_url,
                "created_at": _isoformat(workflow_run.created_at),
                "updated_at": _isoformat(workflow_run.updated_at),
                "run_started_at": _isoformat(
                    getattr(workflow_run, "run_started_at", None)
                ),
                "head_branch": workflow_run.head_branch,
                "head_sha": workflow_run.head_sha,
                "run_number": workflow_run.run_number,
            }
        )
        if len(workflow_runs) >= workflow_limit:
            break

    payload["combined_status"] = combined_status_payload
    payload["check_runs"] = check_runs
    payload["workflow_runs"] = workflow_runs
    return payload


def _build_workflow_run_payload(
    run_payload: dict,
    jobs_payload: dict,
    job_limit: int,
) -> dict:
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


def _isoformat(value) -> Optional[str]:
    return value.isoformat() if value else None
