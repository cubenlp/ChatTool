from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from chattool.client.main import cli as root_cli
from chattool.tools.github.client import GitHubClient
import chattool.tools.github.commands as gh_commands


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fake_pr_checks_payload():
    return {
        "number": 138,
        "title": "Improve setup and CI visibility",
        "state": "open",
        "url": "https://github.com/CubeNLP/ChatTool/pull/138",
        "author": "rex",
        "base": "vibe/master",
        "head": "rex/setup",
        "head_sha": "abc123def456",
        "mergeable": False,
        "mergeable_state": "dirty",
        "combined_status": {
            "state": "pending",
            "sha": "abc123def456",
            "total_count": 1,
            "statuses": [
                {
                    "context": "ci/test",
                    "state": "success",
                    "description": "pytest passed",
                    "target_url": "https://ci.example.com/test",
                    "updated_at": _dt("2026-03-23T10:00:00Z").isoformat(),
                },
            ],
        },
        "check_runs": [],
        "check_runs_error": None,
        "workflow_runs": [],
        "workflow_runs_error": None,
    }


def test_root_cli_no_longer_registers_gh_command():
    runner = CliRunner()

    help_result = runner.invoke(root_cli, ["--help"])
    gh_result = runner.invoke(root_cli, ["gh", "--help"])

    assert help_result.exit_code == 0
    assert "\n  gh " not in help_result.output
    assert gh_result.exit_code != 0
    assert "No such command 'gh'" in gh_result.output


def test_merge_pr_blocks_failed_ci(monkeypatch):
    merge_calls = []
    monkeypatch.setattr(
        gh_commands,
        "resolve_repo_and_credential_path",
        lambda repo: ("CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )
    monkeypatch.setattr(
        gh_commands,
        "get_client",
        lambda token, require_token=False, credential_path=None: object(),
    )
    monkeypatch.setattr(
        gh_commands,
        "get_pr_checks",
        lambda *args, **kwargs: {
            **_fake_pr_checks_payload(),
            "check_runs": [
                {"name": "build", "status": "completed", "conclusion": "failure"}
            ],
            "workflow_runs": [
                {"name": "CI", "status": "completed", "conclusion": "failure"}
            ],
        },
    )
    monkeypatch.setattr(
        gh_commands,
        "post_pr_merge",
        lambda *args, **kwargs: merge_calls.append(True),
    )

    with pytest.raises(Exception) as excinfo:
        gh_commands.merge_pr(None, 138, "merge", None, None, True, None)

    message = str(excinfo.value)
    assert "Refusing to merge because CI checks are not green" in message
    assert "chatgh pr-legacy checks --number 138" in message
    assert not merge_calls


def test_merge_pr_without_check_keeps_current_behavior(monkeypatch):
    monkeypatch.setattr(
        gh_commands,
        "resolve_repo_and_credential_path",
        lambda repo: ("CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )
    monkeypatch.setattr(
        gh_commands,
        "get_client",
        lambda token, require_token=False, credential_path=None: object(),
    )
    monkeypatch.setattr(
        gh_commands,
        "post_pr_merge",
        lambda *args, **kwargs: {
            "merged": True,
            "message": "merged",
            "url": "https://github.com/CubeNLP/ChatTool/pull/138",
        },
    )

    result = gh_commands.merge_pr(None, 138, "merge", None, None, False, None)

    assert result["merged"] is True
    assert result["url"].endswith("/138")


def test_check_pr_wait_loops_until_complete(monkeypatch):
    payloads = iter(
        [
            {
                **_fake_pr_checks_payload(),
                "check_runs": [
                    {"name": "tests", "status": "in_progress", "conclusion": None}
                ],
                "workflow_runs": [],
            },
            {
                **_fake_pr_checks_payload(),
                "combined_status": {
                    "state": "success",
                    "sha": "abc123def456",
                    "total_count": 0,
                    "statuses": [],
                },
                "check_runs": [
                    {"name": "tests", "status": "completed", "conclusion": "success"}
                ],
                "workflow_runs": [],
            },
        ]
    )
    monkeypatch.setattr(
        gh_commands,
        "resolve_repo_and_credential_path",
        lambda repo: ("CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )
    monkeypatch.setattr(
        gh_commands,
        "get_client",
        lambda token, require_token=False, credential_path=None: object(),
    )
    monkeypatch.setattr(gh_commands, "get_pr_checks", lambda *args, **kwargs: next(payloads))
    sleeps = []
    monkeypatch.setattr(gh_commands.time, "sleep", lambda seconds: sleeps.append(seconds))

    payload = gh_commands.check_pr(None, 138, 20, 10, True, 0.01, 1, None)

    assert payload["check_runs"][0]["status"] == "completed"
    assert sleeps == [0.01]


def test_github_client_thin_wrapper_calls_extracted_request(monkeypatch):
    fake_repo = SimpleNamespace(
        get_pull=lambda number: SimpleNamespace(
            number=number,
            title="Test PR",
            state="open",
            html_url="https://github.com/CubeNLP/ChatTool/pull/138",
            user=SimpleNamespace(login="rex"),
            base=SimpleNamespace(ref="main"),
            head=SimpleNamespace(ref="rex/test", sha="abc123"),
            created_at=None,
            updated_at=None,
            merged_at=None,
            mergeable=True,
            mergeable_state="clean",
        )
    )
    monkeypatch.setattr(
        "chattool.tools.github.client.get_client",
        lambda token, require_token=False, credential_path=None: SimpleNamespace(
            get_repo=lambda repo: fake_repo
        ),
    )

    client = GitHubClient(user_name="octocat", token="ghp_test")
    payload = client.get_pr_view("CubeNLP/ChatTool", 138)

    assert payload["number"] == 138
    assert payload["mergeable_state"] == "clean"
