from pathlib import Path

import pytest
from click.testing import CliRunner

from chattool.client.main import cli
import chattool.tools.github.cli as gh_cli


pytestmark = pytest.mark.mock_cli


@pytest.fixture
def runner():
    return CliRunner()


def test_chattool_gh_help_commands(runner):
    result = runner.invoke(cli, ["gh", "--help"])
    assert result.exit_code == 0
    assert "pr" in result.output
    assert "run" in result.output
    assert "repo-perms" in result.output


def test_chattool_gh_pr_help_commands(runner):
    result = runner.invoke(cli, ["gh", "pr", "--help"])
    assert result.exit_code == 0
    for command in ["create", "list", "view", "checks", "comment", "merge", "edit"]:
        assert command in result.output


def test_chattool_gh_pr_view_prompts_for_number(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "view_pr",
        lambda repo, number, token: {
            "number": number,
            "title": "Improve setup and CI visibility",
            "state": "open",
            "url": "https://github.com/CubeNLP/ChatTool/pull/138",
            "author": "rex",
            "created_at": None,
            "updated_at": None,
            "merged_at": None,
            "base": "main",
            "head": "rex/setup",
            "mergeable": False,
            "mergeable_state": "dirty",
        },
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "138",
    )

    result = runner.invoke(cli, ["gh", "pr", "view"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "#138 [open] Improve setup and CI visibility" in result.output


def test_chattool_gh_pr_create_prompts_for_missing_fields(monkeypatch, runner):
    created = {}
    monkeypatch.setattr(
        gh_cli,
        "create_pr",
        lambda repo, base, head, title, body, token: created.update(
            {"base": base, "head": head, "title": title, "body": body}
        )
        or {"url": "https://github.com/CubeNLP/ChatTool/pull/200"},
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    answers = {"base": "main", "head": "rex/feature", "title": "Test PR"}
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )

    result = runner.invoke(cli, ["gh", "pr", "create"], catch_exceptions=False)

    assert result.exit_code == 0
    assert created == {
        "base": "main",
        "head": "rex/feature",
        "title": "Test PR",
        "body": "",
    }


def test_chattool_gh_pr_comment_prompts_for_inputs(monkeypatch, runner):
    created = {}
    monkeypatch.setattr(
        gh_cli,
        "comment_pr",
        lambda repo, number, body, token: created.update({"number": number, "body": body})
        or {"url": "https://github.com/CubeNLP/ChatTool/pull/138#issuecomment-1"},
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    answers = {"pr number": "138", "comment body": "LGTM"}
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )

    result = runner.invoke(cli, ["gh", "pr", "comment"], catch_exceptions=False)

    assert result.exit_code == 0
    assert created == {"number": 138, "body": "LGTM"}


def test_chattool_gh_pr_merge_prompts_for_number(monkeypatch, runner):
    merge_calls = []
    monkeypatch.setattr(
        gh_cli,
        "merge_pr",
        lambda repo, number, method, title, message, check_before_merge, token: merge_calls.append(
            {
                "number": number,
                "method": method,
                "check": check_before_merge,
            }
        )
        or {"url": "https://github.com/CubeNLP/ChatTool/pull/138"},
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "138",
    )

    result = runner.invoke(cli, ["gh", "pr", "merge"], catch_exceptions=False)

    assert result.exit_code == 0
    assert merge_calls == [{"number": 138, "method": "merge", "check": False}]


def test_chattool_gh_run_view_prompts_for_run_id(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "view_run",
        lambda repo, run_id, job_limit, token: {
            "id": run_id,
            "name": "Python Package",
            "display_title": "Python Package / pull_request",
            "event": "pull_request",
            "status": "completed",
            "conclusion": "failure",
            "html_url": "https://github.com/CubeNLP/ChatTool/actions/runs/1",
            "created_at": None,
            "updated_at": None,
            "run_started_at": None,
            "head_branch": "rex/setup",
            "head_sha": "abc123",
            "run_number": 151,
            "jobs_total_count": 0,
            "jobs": [],
        },
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "23494900414",
    )

    result = runner.invoke(cli, ["gh", "run", "view"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Run #151 (id=23494900414): completed/failure" in result.output


def test_chattool_gh_run_logs_prompts_for_job_id(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "view_job_logs",
        lambda repo, job_id, tail, output, token: {
            "job": {
                "id": job_id,
                "name": "build",
                "status": "completed",
                "conclusion": "failure",
                "html_url": None,
                "runner_name": None,
                "runner_group_name": None,
                "labels": [],
                "started_at": None,
                "completed_at": None,
                "steps": [],
            },
            "tail": tail,
            "output_path": output,
            "log": "full log",
            "rendered_log": "line 1\nline 2",
        },
    )
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "68373094563",
    )

    result = runner.invoke(cli, ["gh", "run", "logs"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "build (id=68373094563): completed/failure" in result.output
    assert "line 1" in result.output


def test_chattool_gh_required_commands_error_with_no_interaction(runner):
    result = runner.invoke(cli, ["gh", "pr", "view", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: number" in result.output


def test_chattool_gh_pr_checks_forwards_wait(monkeypatch, runner):
    called = {}
    monkeypatch.setattr(
        gh_cli,
        "check_pr",
        lambda repo, number, check_limit, workflow_limit, wait_for_completion, interval, timeout, token: called.update(
            {
                "number": number,
                "wait": wait_for_completion,
                "interval": interval,
                "timeout": timeout,
            }
        )
        or {
            "number": number,
            "title": "Test PR",
            "state": "open",
            "url": "https://github.com/CubeNLP/ChatTool/pull/138",
            "author": "rex",
            "base": "main",
            "head": "rex/setup",
            "head_sha": "abc123",
            "mergeable": True,
            "mergeable_state": "clean",
            "combined_status": {"state": "success", "total_count": 0, "statuses": []},
            "check_runs": [],
            "workflow_runs": [],
        },
    )

    result = runner.invoke(
        cli,
        ["gh", "pr", "checks", "--number", "138", "--wait", "--interval", "10", "--timeout", "600"],
    )

    assert result.exit_code == 0
    assert called == {"number": 138, "wait": True, "interval": 10.0, "timeout": 600.0}


def test_chattool_gh_pr_merge_forwards_check(monkeypatch, runner):
    called = {}
    monkeypatch.setattr(
        gh_cli,
        "merge_pr",
        lambda repo, number, method, title, message, check_before_merge, token: called.update(
            {"number": number, "method": method, "check": check_before_merge}
        )
        or {"url": "https://github.com/CubeNLP/ChatTool/pull/138"},
    )

    result = runner.invoke(cli, ["gh", "pr", "merge", "--number", "138", "--check"])

    assert result.exit_code == 0
    assert called == {"number": 138, "method": "merge", "check": True}


def test_chattool_gh_repo_perms_basic(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "repo_perms",
        lambda repo, full_json, token: {
            "repo": "CubeNLP/ChatTool",
            "private": True,
            "visibility": "private",
            "permissions": {"pull": True, "push": False, "admin": False},
            "capabilities": {
                "can_comment_pr": False,
                "can_merge_pr": False,
                "can_read_pr": True,
                "can_view_actions": True,
                "can_view_checks": True,
            },
        },
    )

    result = runner.invoke(cli, ["gh", "repo-perms", "--repo", "CubeNLP/ChatTool"])

    assert result.exit_code == 0
    assert "Repo: CubeNLP/ChatTool" in result.output
    assert "Permissions:" in result.output
    assert "Capabilities:" in result.output


def test_chattool_gh_repo_perms_full_json(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "repo_perms",
        lambda repo, full_json, token: {
            "repo": "CubeNLP/ChatTool",
            "private": False,
            "visibility": "public",
            "permissions": {"pull": True, "push": True, "admin": True},
            "capabilities": {"can_merge_pr": True},
            "repository": {"allow_merge_commit": True},
        },
    )

    result = runner.invoke(
        cli,
        ["gh", "repo-perms", "--repo", "CubeNLP/ChatTool", "--json-output", "--full-json"],
    )

    assert result.exit_code == 0
    assert '"repository"' in result.output
    assert '"allow_merge_commit": true' in result.output


def test_chattool_gh_repo_scoped_credential_requires_exact_path(monkeypatch, runner):
    monkeypatch.setattr(
        "chattool.tools.github.api.read_github_token_from_credentials",
        lambda credential_path=None, exact_only=False: None if credential_path and exact_only else "ghp_other_repo_token",
    )
    from chattool.tools.github.api import resolve_token

    assert resolve_token(None, credential_path="CubeNLP/ChatTool.git", exact_only=True) is None


def test_chattool_gh_set_token_configures_repo_scoped_https_credential(tmp_path, monkeypatch, runner):
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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_test_token"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Configured Git HTTPS token for CubeNLP/ChatTool." in result.output
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "path=CubeNLP/ChatTool.git" in approve_input
    assert "password=ghp_test_token" in approve_input


def test_chattool_gh_set_token_save_env_updates_github_env(tmp_path, monkeypatch, runner):
    env_root = tmp_path / "envs"
    monkeypatch.setattr("chattool.tools.github.api.CHATTOOL_ENV_DIR", env_root)

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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_saved_token", "--save-env"], catch_exceptions=False)

    assert result.exit_code == 0
    env_file = Path(env_root) / "GitHub" / ".env"
    assert env_file.exists()
    assert "GITHUB_ACCESS_TOKEN='ghp_saved_token'" in env_file.read_text(encoding="utf-8")


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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_test_token"])

    assert result.exit_code != 0
    assert "Current repository does not have a recognizable GitHub remote." in result.output


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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)
    monkeypatch.delenv("GITHUB_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(gh_cli, "resolve_token", lambda token, credential_path=None, exact_only=False: token)
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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_test_token"], catch_exceptions=False)

    assert result.exit_code == 0
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "path=CubeNLP/ChatTool.git" in approve_input


def test_chattool_gh_set_token_keeps_remote_path_without_git_suffix(monkeypatch, runner):
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

    monkeypatch.setattr("chattool.tools.github.api.subprocess.run", fake_run)

    result = runner.invoke(cli, ["gh", "set-token", "--token", "ghp_test_token"], catch_exceptions=False)

    assert result.exit_code == 0
    approve_input = inputs[commands.index(["git", "credential", "approve"])]
    assert "path=Lean-zh/LeanUp\n" in approve_input
