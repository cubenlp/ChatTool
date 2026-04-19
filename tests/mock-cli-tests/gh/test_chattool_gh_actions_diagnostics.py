import pytest
from click.testing import CliRunner

from chattool.client.main import cli
import chattool.tools.github.cli as gh_cli


pytestmark = pytest.mark.mock_cli


@pytest.fixture
def runner():
    return CliRunner()


def test_chattool_gh_run_view_basic(monkeypatch, runner):
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
            "html_url": "https://github.com/CubeNLP/ChatTool/actions/runs/23494900414",
            "created_at": "2026-03-24T01:15:00Z",
            "updated_at": "2026-03-24T01:18:00Z",
            "run_started_at": "2026-03-24T01:15:30Z",
            "head_branch": "rex/fix-ci-after-feishu",
            "head_sha": "b4a242b43599a6d0015442c63b2836de211b6273",
            "run_number": 151,
            "jobs_total_count": 1,
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
                            "number": 9,
                            "name": "Check test results",
                            "status": "completed",
                            "conclusion": "failure",
                        }
                    ],
                }
            ],
        },
    )

    result = runner.invoke(cli, ["gh", "run", "view", "--run-id", "23494900414"])

    assert result.exit_code == 0
    assert "Run #151 (id=23494900414): completed/failure" in result.output
    assert "Jobs (1/1 shown):" in result.output
    assert "[9] Check test results: completed/failure" in result.output


def test_chattool_gh_run_logs_basic(monkeypatch, runner):
    monkeypatch.setattr(
        gh_cli,
        "view_job_logs",
        lambda repo, job_id, tail, output, token: {
            "job": {
                "id": job_id,
                "name": "build (3.10, ubuntu-latest)",
                "status": "completed",
                "conclusion": "failure",
                "html_url": "https://github.com/CubeNLP/ChatTool/actions/runs/23494900414/job/68373094563",
                "runner_name": "GitHub Actions 7",
                "runner_group_name": "GitHub Actions",
                "labels": ["ubuntu-latest"],
                "started_at": None,
                "completed_at": None,
                "steps": [],
            },
            "tail": tail,
            "output_path": None,
            "log": "full log",
            "rendered_log": "FAILED tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant\nError: Process completed with exit code 1.",
        },
    )

    result = runner.invoke(cli, ["gh", "run", "logs", "--job-id", "68373094563", "--tail", "2"])

    assert result.exit_code == 0
    assert "build (3.10, ubuntu-latest) (id=68373094563): completed/failure" in result.output
    assert "FAILED tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant" in result.output
