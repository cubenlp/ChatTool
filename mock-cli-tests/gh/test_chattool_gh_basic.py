from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from chattool.client.main import cli
import chattool.tools.github.cli as gh_cli


pytestmark = pytest.mark.mock_cli


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

    monkeypatch.setattr(
        gh_cli, "_get_client", lambda token, require_token=False: client
    )
    monkeypatch.setattr(
        gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool"
    )


def _install_fake_merge_client(monkeypatch):
    merge_calls = []
    pr = _fake_pr()

    def merge(**payload):
        merge_calls.append(payload)
        return SimpleNamespace(merged=True, message="merged")

    pr.merge = merge
    commit = SimpleNamespace(
        get_combined_status=lambda: SimpleNamespace(
            state="pending", sha="abc123def456", total_count=0, statuses=[]
        ),
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

    monkeypatch.setattr(
        gh_cli, "_get_client", lambda token, require_token=False: client
    )
    monkeypatch.setattr(
        gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool"
    )
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

    result = runner.invoke(
        cli, ["gh", "pr-merge", "--number", "138", "--confirm", "--check"]
    )

    assert result.exit_code != 0
    assert "Refusing to merge because CI checks are not green" in result.output
    assert "workflow Python Package concluded failure" in result.output
    assert not merge_calls


def test_chattool_gh_repo_perms_basic(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool"
    )
    monkeypatch.setattr(
        gh_cli,
        "_github_api_get_json",
        lambda repo, path, token, params=None: {
            "full_name": "CubeNLP/ChatTool",
            "private": True,
            "visibility": "private",
            "permissions": {"pull": True, "push": False, "admin": False},
        },
    )

    result = runner.invoke(cli, ["gh", "repo-perms", "--repo", "CubeNLP/ChatTool"])

    assert result.exit_code == 0
    assert "Repo: CubeNLP/ChatTool" in result.output
    assert "Permissions:" in result.output
    assert "  - admin: False" in result.output
    assert "  - pull: True" in result.output
    assert "  - push: False" in result.output


def test_chattool_gh_set_token_configures_repo_scoped_https_credential(
    tmp_path, monkeypatch, runner
):
    commands = []
    inputs = []

    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        commands.append(command)
        inputs.append(input)

        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="git@github.com:CubeNLP/ChatTool.git\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli,
        ["gh", "set-token", "--token", "ghp_test_token"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Configured Git HTTPS token for CubeNLP/ChatTool." in result.output
    assert ["git", "config", "--global", "credential.helper", "store"] in commands
    assert ["git", "config", "--global", "credential.useHttpPath", "true"] in commands
    assert ["git", "credential", "approve"] in commands
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "protocol=https" in approve_input
    assert "host=github.com" in approve_input
    assert "path=CubeNLP/ChatTool.git" in approve_input
    assert "username=x-access-token" in approve_input
    assert "password=ghp_test_token" in approve_input


def test_chattool_gh_set_token_save_env_updates_github_env(
    tmp_path, monkeypatch, runner
):
    env_root = tmp_path / "envs"
    monkeypatch.setattr(gh_cli, "CHATTOOL_ENV_DIR", env_root)

    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="https://github.com/CubeNLP/ChatTool.git\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli,
        ["gh", "set-token", "--token", "ghp_saved_token", "--save-env"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    env_file = Path(env_root) / "GitHub" / ".env"
    assert env_file.exists()
    assert "GITHUB_ACCESS_TOKEN='ghp_saved_token'" in env_file.read_text(
        encoding="utf-8"
    )


def test_chattool_gh_set_token_rejects_non_github_remote(monkeypatch, runner):
    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="git@gitlab.com:CubeNLP/ChatTool.git\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_test_token"])

    assert result.exit_code != 0
    assert (
        "Current repository does not have a recognizable GitHub remote."
        in result.output
    )


def test_chattool_gh_set_token_prompts_for_missing_token_in_tty(monkeypatch, runner):
    commands = []
    inputs = []

    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        commands.append(command)
        inputs.append(input)

        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="git@github.com:CubeNLP/ChatTool.git\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)
    monkeypatch.delenv("GITHUB_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(gh_cli.GitHubConfig.GITHUB_ACCESS_TOKEN, "value", None)
    monkeypatch.setattr(gh_cli, "is_interactive_available", lambda: True)
    monkeypatch.setattr(
        gh_cli,
        "ask_text",
        lambda message, default="", password=False, style=None: "ghp_prompted_token",
    )

    result = runner.invoke(cli, ["gh", "set-token"], catch_exceptions=False)

    assert result.exit_code == 0
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "password=ghp_prompted_token" in approve_input


def test_chattool_gh_set_token_falls_back_to_other_github_remote(monkeypatch, runner):
    commands = []
    inputs = []

    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        commands.append(command)
        inputs.append(input)

        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\nupstream\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="git@gitlab.com:CubeNLP/ChatTool.git\n")
        if command == ["git", "remote", "get-url", "upstream"]:
            return Result(stdout="git@github.com:CubeNLP/ChatTool.git\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli,
        ["gh", "set-token", "--token", "ghp_test_token"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Configured Git HTTPS token for CubeNLP/ChatTool." in result.output
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "path=CubeNLP/ChatTool.git" in approve_input


def test_chattool_gh_set_token_keeps_remote_path_without_git_suffix(
    monkeypatch, runner
):
    commands = []
    inputs = []

    def fake_run(command, check=True, capture_output=True, text=True, input=None):
        commands.append(command)
        inputs.append(input)

        class Result:
            def __init__(self, stdout=""):
                self.stdout = stdout
                self.stderr = ""

        if command == ["git", "remote"]:
            return Result(stdout="origin\n")
        if command == ["git", "remote", "get-url", "origin"]:
            return Result(stdout="https://github.com/Lean-zh/LeanUp\n")
        return Result()

    monkeypatch.setattr(gh_cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli,
        ["gh", "set-token", "--token", "ghp_test_token"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "path=Lean-zh/LeanUp\n" in approve_input
