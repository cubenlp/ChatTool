from __future__ import annotations

import click


def derive_repo_capabilities(permissions: dict) -> dict:
    pull = bool(permissions.get("pull"))
    push = bool(permissions.get("push"))
    admin = bool(permissions.get("admin"))
    maintain = bool(permissions.get("maintain"))
    triage = bool(permissions.get("triage"))
    return {
        "can_read_pr": pull,
        "can_comment_pr": triage or push or maintain or admin,
        "can_merge_pr": push or maintain or admin,
        "can_view_checks": pull,
        "can_view_actions": pull,
    }


def echo_pr_list(items: list[dict]) -> None:
    if not items:
        click.echo("No pull requests found.")
        return
    for item in items:
        click.echo(f"#{item['number']} [{item['state']}] {item['title']} ({item['author']})")
        click.echo(f"  {item['url']}")


def echo_pr_view(payload: dict) -> None:
    click.echo(f"#{payload['number']} [{payload['state']}] {payload['title']}")
    click.echo(f"Author: {payload['author']}")
    click.echo(f"URL: {payload['url']}")
    click.echo(f"Base: {payload['base']}  Head: {payload['head']}")
    click.echo(
        f"Mergeable: {format_optional(payload['mergeable'])}  "
        f"Merge State: {format_optional(payload['mergeable_state'])}"
    )
    click.echo(f"Created: {payload['created_at']}  Updated: {payload['updated_at']}")
    click.echo(f"Merged: {payload['merged_at']}")


def echo_pr_checks(payload: dict) -> None:
    click.echo(f"#{payload['number']} [{payload['state']}] {payload['title']}")
    click.echo(f"Author: {payload['author']}")
    click.echo(f"URL: {payload['url']}")
    click.echo(f"Base: {payload['base']}  Head: {payload['head']}")
    click.echo(f"Head SHA: {payload['head_sha']}")
    click.echo(
        f"Mergeable: {format_optional(payload['mergeable'])}  "
        f"Merge State: {format_optional(payload['mergeable_state'])}"
    )

    combined = payload["combined_status"]
    click.echo(
        f"Combined status: {combined['state']} "
        f"({combined['total_count']} status{'es' if combined['total_count'] != 1 else ''})"
    )
    if combined.get("error"):
        click.echo(f"  note: {combined['error']}")

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
            click.echo(
                f"  - {check_run['name']}: {check_run['status']}/{conclusion}{app}"
            )
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


def echo_workflow_run(payload: dict) -> None:
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
            echo_workflow_job(job, prefix="  - ")
    else:
        click.echo("Jobs: none")


def echo_workflow_job(payload: dict, prefix: str = "") -> None:
    conclusion = payload["conclusion"] or "-"
    click.echo(
        f"{prefix}{payload['name']} (id={payload['id']}): {payload['status']}/{conclusion}"
    )
    if payload["html_url"]:
        click.echo(f"{prefix}  {payload['html_url']}")
    runner_bits = [
        bit for bit in [payload["runner_name"], payload["runner_group_name"]] if bit
    ]
    if runner_bits:
        click.echo(f"{prefix}  runner: {' / '.join(runner_bits)}")
    if payload["labels"]:
        click.echo(f"{prefix}  labels: {', '.join(payload['labels'])}")
    if payload["steps"]:
        click.echo(f"{prefix}  steps:")
        for step in payload["steps"]:
            step_conclusion = step["conclusion"] or "-"
            click.echo(
                f"{prefix}    - [{step['number']}] {step['name']}: {step['status']}/{step_conclusion}"
            )


def collect_merge_blockers(payload: dict) -> list[str]:
    blockers: list[str] = []
    if payload["mergeable"] is False:
        blockers.append("pull request is not mergeable against the current base branch")

    merge_state = payload["mergeable_state"]
    if merge_state in {"dirty", "blocked", "behind", "draft", "unknown"}:
        blockers.append(f"pull request merge state is {merge_state}")

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
            blockers.append(
                f"check run {check_run['name']} concluded {conclusion or 'unknown'}"
            )

    for workflow_run in payload["workflow_runs"]:
        status = workflow_run["status"]
        conclusion = workflow_run["conclusion"]
        if status != "completed":
            blockers.append(f"workflow {workflow_run['name']} is {status}")
            continue
        if conclusion not in {"success", "neutral", "skipped"}:
            blockers.append(
                f"workflow {workflow_run['name']} concluded {conclusion or 'unknown'}"
            )

    return blockers


def has_incomplete_pr_checks(payload: dict) -> bool:
    for status in payload["combined_status"]["statuses"]:
        if status["state"] == "pending":
            return True
    for check_run in payload["check_runs"]:
        if check_run["status"] != "completed":
            return True
    for workflow_run in payload["workflow_runs"]:
        if workflow_run["status"] != "completed":
            return True
    return False


def format_optional(value) -> str:
    return "-" if value is None else str(value)


def tail_text(text: str, tail: int) -> str:
    if tail == 0:
        return text
    lines = text.splitlines()
    if len(lines) <= tail:
        return text
    return "\n".join(lines[-tail:])
