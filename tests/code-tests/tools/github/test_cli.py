from datetime import datetime, timezone
from types import SimpleNamespace

from click.testing import CliRunner

from chattool.client.main import cli as root_cli
import chattool.tools.github.cli as gh_cli


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
        mergeable=False,
        mergeable_state="dirty",
        created_at=_dt("2026-03-23T09:40:00Z"),
        updated_at=_dt("2026-03-23T10:05:00Z"),
        merged_at=None,
    )


def _fake_commit():
    combined_status = SimpleNamespace(
        state="pending",
        sha="abc123def456",
        total_count=2,
        statuses=[
            SimpleNamespace(
                context="ci/test",
                state="success",
                description="pytest passed",
                target_url="https://ci.example.com/test",
                updated_at=_dt("2026-03-23T10:00:00Z"),
            ),
            SimpleNamespace(
                context="ci/lint",
                state="pending",
                description="ruff running",
                target_url="https://ci.example.com/lint",
                updated_at=_dt("2026-03-23T10:05:00Z"),
            ),
        ],
    )

    check_runs = [
        SimpleNamespace(
            name="tests",
            status="completed",
            conclusion="success",
            details_url="https://github.com/CubeNLP/ChatTool/actions/runs/1/job/11",
            html_url="https://github.com/CubeNLP/ChatTool/runs/11",
            app=SimpleNamespace(name="GitHub Actions"),
            started_at=_dt("2026-03-23T09:55:00Z"),
            completed_at=_dt("2026-03-23T10:00:00Z"),
        ),
        SimpleNamespace(
            name="lint",
            status="in_progress",
            conclusion=None,
            details_url="https://github.com/CubeNLP/ChatTool/actions/runs/1/job/12",
            html_url="https://github.com/CubeNLP/ChatTool/runs/12",
            app=SimpleNamespace(name="GitHub Actions"),
            started_at=_dt("2026-03-23T10:01:00Z"),
            completed_at=None,
        ),
    ]

    return SimpleNamespace(
        get_combined_status=lambda: combined_status,
        get_check_runs=lambda: iter(check_runs),
    )


def _fake_workflow_runs():
    return [
        SimpleNamespace(
            name="CI",
            display_title="CI / tests",
            event="pull_request",
            status="in_progress",
            conclusion=None,
            html_url="https://github.com/CubeNLP/ChatTool/actions/runs/1",
            created_at=_dt("2026-03-23T09:50:00Z"),
            updated_at=_dt("2026-03-23T10:05:00Z"),
            run_started_at=_dt("2026-03-23T09:51:00Z"),
            head_branch="rex/setup",
            head_sha="abc123def456",
            run_number=501,
        )
    ]


def _install_fake_client(monkeypatch):
    pr = _fake_pr()
    commit = _fake_commit()
    workflow_runs = _fake_workflow_runs()

    repo_obj = SimpleNamespace(
        get_pull=lambda number: pr,
        get_commit=lambda sha: commit,
        get_workflow_runs=lambda head_sha=None: iter(workflow_runs),
    )
    client = SimpleNamespace(get_repo=lambda repo: repo_obj)

    monkeypatch.setattr(
        gh_cli,
        "get_client",
        lambda token, require_token=False, credential_path=None: client,
    )
    monkeypatch.setattr(
        gh_cli,
        "_resolve_repo_and_credential_path",
        lambda repo: (repo or "CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )


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
    job_payload = jobs_payload["jobs"][0]
    logs_text = "\n".join(
        [
            "=========================== short test summary info ============================",
            "FAILED tests/code-tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant",
            "Error: Process completed with exit code 1.",
        ]
    )

    def fake_json(repo, path, token, params=None):
        if path == "/actions/runs/23494900414":
            return run_payload
        if path == "/actions/runs/23494900414/jobs":
            return jobs_payload
        if path == "/actions/jobs/68373094563":
            return job_payload
        raise AssertionError(f"Unexpected JSON path: {path}")

    def fake_text(repo, path, token, params=None):
        if path == "/actions/jobs/68373094563/logs":
            return logs_text
        raise AssertionError(f"Unexpected text path: {path}")

    monkeypatch.setattr(
        gh_cli,
        "_resolve_repo_and_credential_path",
        lambda repo: (repo or "CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )
    monkeypatch.setattr(
        gh_cli, "resolve_token", lambda token, credential_path=None: token or "ghp_test"
    )
    monkeypatch.setattr(gh_cli, "github_api_get_json", fake_json)
    monkeypatch.setattr(gh_cli, "github_api_get_text", fake_text)


def _install_fake_merge_client(
    monkeypatch,
    *,
    check_status="completed",
    check_conclusion="success",
    workflow_status="completed",
    workflow_conclusion="success",
):
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
                    status=check_status,
                    conclusion=check_conclusion
                    if check_status == "completed"
                    else None,
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
                    status=workflow_status,
                    conclusion=workflow_conclusion
                    if workflow_status == "completed"
                    else None,
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
        gh_cli,
        "get_client",
        lambda token, require_token=False, credential_path=None: client,
    )
    monkeypatch.setattr(
        gh_cli,
        "_resolve_repo_and_credential_path",
        lambda repo: (repo or "CubeNLP/ChatTool", "CubeNLP/ChatTool.git"),
    )
    return merge_calls


def test_root_cli_registers_pr_check_command():
    runner = CliRunner()

    result = runner.invoke(root_cli, ["gh", "--help"])

    assert result.exit_code == 0
    assert "pr-check" in result.output
    assert "run-view" in result.output
    assert "job-logs" in result.output


def test_pr_check_command_renders_summary(monkeypatch):
    runner = CliRunner()
    _install_fake_client(monkeypatch)

    result = runner.invoke(gh_cli.cli, ["pr-check", "--number", "138"])

    assert result.exit_code == 0
    assert "#138 [open] Improve setup and CI visibility" in result.output
    assert "Mergeable: False  Merge State: dirty" in result.output
    assert "Combined status: pending (2 statuses)" in result.output
    assert "Statuses:" in result.output
    assert "ci/test: success - pytest passed" in result.output
    assert "Check runs:" in result.output
    assert "tests: completed/success [GitHub Actions]" in result.output
    assert "Workflow runs:" in result.output
    assert "CI: in_progress/- (event=pull_request, run=501)" in result.output


def test_pr_check_command_supports_json_output(monkeypatch):
    runner = CliRunner()
    _install_fake_client(monkeypatch)

    result = runner.invoke(gh_cli.cli, ["pr-check", "--number", "138", "--json-output"])

    assert result.exit_code == 0
    assert '"number": 138' in result.output
    assert '"mergeable": false' in result.output
    assert '"mergeable_state": "dirty"' in result.output
    assert '"head_sha": "abc123def456"' in result.output
    assert '"state": "pending"' in result.output
    assert '"context": "ci/test"' in result.output
    assert '"name": "tests"' in result.output
    assert '"run_number": 501' in result.output


def test_pr_view_command_renders_mergeability(monkeypatch):
    runner = CliRunner()
    _install_fake_client(monkeypatch)

    result = runner.invoke(gh_cli.cli, ["pr-view", "--number", "138"])

    assert result.exit_code == 0
    assert "#138 [open] Improve setup and CI visibility" in result.output
    assert "Mergeable: False  Merge State: dirty" in result.output


def test_pr_view_command_supports_json_output(monkeypatch):
    runner = CliRunner()
    _install_fake_client(monkeypatch)

    result = runner.invoke(gh_cli.cli, ["pr-view", "--number", "138", "--json-output"])

    assert result.exit_code == 0
    assert '"number": 138' in result.output
    assert '"mergeable": false' in result.output
    assert '"mergeable_state": "dirty"' in result.output


def test_run_view_command_renders_jobs(monkeypatch):
    runner = CliRunner()
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(gh_cli.cli, ["run-view", "--run-id", "23494900414"])

    assert result.exit_code == 0
    assert "Run #151 (id=23494900414): completed/failure" in result.output
    assert "Jobs (1/1 shown):" in result.output
    assert (
        "build (3.10, ubuntu-latest) (id=68373094563): completed/failure"
        in result.output
    )
    assert "[9] Check test results: completed/failure" in result.output


def test_run_view_command_supports_json_output(monkeypatch):
    runner = CliRunner()
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(
        gh_cli.cli, ["run-view", "--run-id", "23494900414", "--json-output"]
    )

    assert result.exit_code == 0
    assert '"id": 23494900414' in result.output
    assert '"jobs_total_count": 1' in result.output
    assert '"name": "build (3.10, ubuntu-latest)"' in result.output


def test_job_logs_command_renders_tail(monkeypatch):
    runner = CliRunner()
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(
        gh_cli.cli, ["job-logs", "--job-id", "68373094563", "--tail", "2"]
    )

    assert result.exit_code == 0
    assert (
        "build (3.10, ubuntu-latest) (id=68373094563): completed/failure"
        in result.output
    )
    assert (
        "FAILED tests/code-tests/skills/test_skill_assets.py::test_all_skills_have_chinese_variant"
        in result.output
    )
    assert "short test summary info" not in result.output


def test_job_logs_command_writes_output(monkeypatch):
    runner = CliRunner()
    _install_fake_actions_api(monkeypatch)

    with runner.isolated_filesystem():
        result = runner.invoke(
            gh_cli.cli,
            [
                "job-logs",
                "--job-id",
                "68373094563",
                "--output",
                "job.log",
                "--tail",
                "1",
            ],
        )

        assert result.exit_code == 0
        assert "Saved full log to: job.log" in result.output
        with open("job.log", "r", encoding="utf-8") as handle:
            assert "short test summary info" in handle.read()


def test_job_logs_command_supports_json_output(monkeypatch):
    runner = CliRunner()
    _install_fake_actions_api(monkeypatch)

    result = runner.invoke(
        gh_cli.cli, ["job-logs", "--job-id", "68373094563", "--json-output"]
    )

    assert result.exit_code == 0
    assert '"output_path": null' in result.output
    assert '"tail": 200' in result.output
    assert (
        '"log": "=========================== short test summary info' in result.output
    )


def test_pr_merge_check_blocks_failed_ci(monkeypatch):
    runner = CliRunner()
    merge_calls = _install_fake_merge_client(
        monkeypatch,
        check_status="completed",
        check_conclusion="failure",
        workflow_status="completed",
        workflow_conclusion="failure",
    )

    result = runner.invoke(gh_cli.cli, ["pr-merge", "--number", "138", "--check"])

    assert result.exit_code != 0
    assert "Refusing to merge because CI checks are not green" in result.output
    assert "check run build concluded failure" in result.output
    assert "workflow Python Package concluded failure" in result.output
    assert not merge_calls


def test_pr_merge_check_blocks_unmergeable_pr(monkeypatch):
    runner = CliRunner()
    merge_calls = _install_fake_merge_client(
        monkeypatch,
        check_status="completed",
        check_conclusion="success",
        workflow_status="completed",
        workflow_conclusion="success",
    )

    result = runner.invoke(gh_cli.cli, ["pr-merge", "--number", "138", "--check"])

    assert result.exit_code != 0
    assert "Refusing to merge because CI checks are not green" in result.output
    assert (
        "pull request is not mergeable against the current base branch" in result.output
    )
    assert "pull request merge state is dirty" in result.output
    assert not merge_calls


def test_pr_merge_without_check_keeps_current_behavior(monkeypatch):
    runner = CliRunner()
    merge_calls = _install_fake_merge_client(
        monkeypatch,
        check_status="completed",
        check_conclusion="failure",
        workflow_status="completed",
        workflow_conclusion="failure",
    )

    result = runner.invoke(gh_cli.cli, ["pr-merge", "--number", "138"])

    assert result.exit_code == 0
    assert "PR merged:" in result.output
    assert merge_calls
