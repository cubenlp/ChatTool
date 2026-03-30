import pytest
from click.testing import CliRunner

from chattool.client.main import cli
import chattool.tools.github.cli as gh_cli


pytestmark = pytest.mark.mock_cli


def _install_fake_actions_api(monkeypatch):
    run_payload = {
        "id": 23494900414,
        "name": "Python Package",
        "display_title": "Python Package / pull_request",
        "event": "pull_request",
        "status": "completed",
        "conclusion": "failure",
        "html_url": "https://github.com/CubeNLP/ChatTool/actions/runs/23494900414",
        "created_at": "2026-03-24T01:15:00Z",
        "updated_at": "2026-03-24T01:18:00Z",
        "run_started_at": "2026-03-24T01:15:30Z",
        "head_branch": "rex/fix-ci-after-feishu",
        "head_sha": "b4a242b43599a6d0015442c63b2836de211b6273",
        "run_number": 151,
    }
    jobs_payload = {
        "total_count": 1,
        "jobs": [
            {
                "id": 68373094563,
                "name": "build (3.10, ubuntu-latest)",
                "status": "completed",
                "conclusion": "failure",
                "html_url": "https://github.com/CubeNLP/ChatTool/actions/runs/23494900414/job/68373094563",
                "runner_name": "GitHub Actions 7",
                "runner_group_name": "GitHub Actions",
                "labels": ["ubuntu-latest"],
                "started_at": "2026-03-24T01:15:40Z",
                "completed_at": "2026-03-24T01:17:00Z",
                "steps": [
                    {
                        "number": 8,
                        "name": "Test CLI docs and real flows",
                        "status": "completed",
                        "conclusion": "success",
                    },
                    {
                        "number": 9,
                        "name": "Check test results",
                        "status": "completed",
                        "conclusion": "failure",
                    },
                ],
            }
        ],
    }
    logs_text = "\n".join(
        [
            "=========================== short test summary info ============================",
            "FAILED tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant",
            "Error: Process completed with exit code 1.",
        ]
    )

    def fake_json(repo, path, token, params=None):
        if path == "/actions/runs/23494900414":
            return run_payload
        if path == "/actions/runs/23494900414/jobs":
            return jobs_payload
        if path == "/actions/jobs/68373094563":
            return jobs_payload["jobs"][0]
        raise AssertionError(f"Unexpected JSON path: {path}")

    def fake_text(repo, path, token, params=None):
        if path == "/actions/jobs/68373094563/logs":
            return logs_text
        raise AssertionError(f"Unexpected text path: {path}")

    monkeypatch.setattr(gh_cli, "_resolve_repo", lambda repo: repo or "CubeNLP/ChatTool")
    monkeypatch.setattr(gh_cli, "_resolve_token", lambda token: token or "ghp_test")
    monkeypatch.setattr(gh_cli, "_github_api_get_json", fake_json)
    monkeypatch.setattr(gh_cli, "_github_api_get_text", fake_text)


@pytest.fixture
def runner():
    return CliRunner()


def test_chattool_gh_run_view_basic(monkeypatch, runner):
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(cli, ["gh", "run-view", "--run-id", "23494900414"])

    assert result.exit_code == 0
    assert "Run #151 (id=23494900414): completed/failure" in result.output
    assert "Jobs (1/1 shown):" in result.output
    assert "build (3.10, ubuntu-latest) (id=68373094563): completed/failure" in result.output
    assert "[9] Check test results: completed/failure" in result.output


def test_chattool_gh_job_logs_basic(monkeypatch, runner):
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(cli, ["gh", "job-logs", "--job-id", "68373094563", "--tail", "2"])

    assert result.exit_code == 0
    assert "build (3.10, ubuntu-latest) (id=68373094563): completed/failure" in result.output
    assert "FAILED tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant" in result.output
    assert "short test summary info" not in result.output
