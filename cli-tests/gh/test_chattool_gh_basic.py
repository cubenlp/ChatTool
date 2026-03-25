from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from chattool.client.main import cli
import chattool.tools.github.cli as gh_cli


pytestmark = pytest.mark.e2e


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fake_pr():
    return SimpleNamespace(
        number=138,
        title="Improve setup and CI visibility",
        state="open",
        html_url="https://github.com/CubeNLP/ChatTool/pull/138",
        user=SimpleNamespace(login="rex"),
        base=SimpleNamespace(ref="vibe/master"),
        head=SimpleNamespace(ref="rex/setup", sha="abc123def456"),
    )


def _install_fake_client(monkeypatch):
    combined_status = SimpleNamespace(
        state="pending",
        sha="abc123def456",
        total_count=1,
        statuses=[
            SimpleNamespace(
                context="ci/test",
                state="success",
                description="pytest passed",
                target_url="https://ci.example.com/test",
                updated_at=_dt("2026-03-23T10:00:00Z"),
            )
        ],
    )
    commit = SimpleNamespace(
        get_combined_status=lambda: combined_status,
        get_check_runs=lambda: iter(
            [
                SimpleNamespace(
                    name="tests",
                    status="completed",
                    conclusion="success",
                    details_url="https://github.com/CubeNLP/ChatTool/actions/runs/1/job/11",
                    html_url="https://github.com/CubeNLP/ChatTool/runs/11",
                    app=SimpleNamespace(name="GitHub Actions"),
                    started_at=_dt("2026-03-23T09:55:00Z"),
                    completed_at=_dt("2026-03-23T10:00:00Z"),
                )
            ]
        ),
    )
    workflow_runs = [
        SimpleNamespace(
            name="CI",
            display_title="CI / tests",
            event="pull_request",
            status="completed",
            conclusion="success",
            html_url="https://github.com/CubeNLP/ChatTool/actions/runs/1",
            created_at=_dt("2026-03-23T09:50:00Z"),
            updated_at=_dt("2026-03-23T10:05:00Z"),
            run_started_at=_dt("2026-03-23T09:51:00Z"),
            head_branch="rex/setup",
            head_sha="abc123def456",
            run_number=501,
        )
    ]
    pr = _fake_pr()
    repo_obj = SimpleNamespace(
        get_pull=lambda number: pr,
        get_commit=lambda sha: commit,
        get_workflow_runs=lambda head_sha=None: iter(workflow_runs),
    )
    client = SimpleNamespace(get_repo=lambda repo: repo_obj)

    monkeypatch.setattr(gh_cli, "_get_client", lambda token, require_token=False: client)
    monkeypatch.setattr(gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool")


def _install_fake_merge_client(monkeypatch):
    merge_calls = []
    pr = _fake_pr()

    def merge(**payload):
        merge_calls.append(payload)
        return SimpleNamespace(merged=True, message="merged")

    pr.merge = merge
    commit = SimpleNamespace(
        get_combined_status=lambda: SimpleNamespace(state="pending", sha="abc123def456", total_count=0, statuses=[]),
        get_check_runs=lambda: iter(
            [
                SimpleNamespace(
                    name="build",
                    status="completed",
                    conclusion="failure",
                    details_url=None,
                    html_url=None,
                    app=SimpleNamespace(name="GitHub Actions"),
                    started_at=None,
                    completed_at=None,
                )
            ]
        ),
    )
    repo_obj = SimpleNamespace(
        get_pull=lambda number: pr,
        get_commit=lambda sha: commit,
        get_workflow_runs=lambda head_sha=None: iter(
            [
                SimpleNamespace(
                    name="Python Package",
                    display_title="Python Package",
                    event="pull_request",
                    status="completed",
                    conclusion="failure",
                    html_url="https://github.com/CubeNLP/ChatTool/actions/runs/1",
                    created_at=None,
                    updated_at=None,
                    run_started_at=None,
                    head_branch="rex/setup",
                    head_sha="abc123def456",
                    run_number=501,
                )
            ]
        ),
    )
    client = SimpleNamespace(get_repo=lambda repo: repo_obj)

    monkeypatch.setattr(gh_cli, "_get_client", lambda token, require_token=False: client)
    monkeypatch.setattr(gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool")
    return merge_calls


@pytest.fixture
def runner():
    return CliRunner()


def test_chattool_gh_help_commands(runner):
    result = runner.invoke(cli, ["gh", "--help"])
    assert result.exit_code == 0
    assert "pr-check" in result.output
    assert "pr-merge" in result.output


def test_chattool_gh_pr_check_basic(monkeypatch, runner):
    _install_fake_client(monkeypatch)

    result = runner.invoke(cli, ["gh", "pr-check", "--number", "138"])

    assert result.exit_code == 0
    assert "#138 [open] Improve setup and CI visibility" in result.output
    assert "Combined status: pending (1 status)" in result.output
    assert "tests: completed/success [GitHub Actions]" in result.output
    assert "CI: completed/success (event=pull_request, run=501)" in result.output


def test_chattool_gh_pr_merge_check_basic(monkeypatch, runner):
    merge_calls = _install_fake_merge_client(monkeypatch)

    result = runner.invoke(cli, ["gh", "pr-merge", "--number", "138", "--confirm", "--check"])

    assert result.exit_code != 0
    assert "Refusing to merge because CI checks are not green" in result.output
    assert "workflow Python Package concluded failure" in result.output
    assert not merge_calls
