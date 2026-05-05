import pytest
from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_hermes_dry_run_registers_and_plans_install():
    result = CliRunner().invoke(
        cli,
        [
            "setup",
            "hermes",
            "--agent-dir",
            "/tmp/chattool-hermes-agent",
            "--webui-dir",
            "/tmp/chattool-hermes-webui",
            "--api-key",
            "test-key",
            "--base-url",
            "http://example.test/v1",
            "--model",
            "test-model",
            "--skip-feishu",
            "--no-webui",
            "--dry-run",
            "-I",
        ],
    )

    assert result.exit_code == 0
    assert "Hermes agent dir:" in result.output
    assert "chattool-hermes-agent" in result.output
    assert "git clone https://github.com/NousResearch/hermes-agent.git" in result.output
    assert "uv pip install" in result.output
    assert "Would write Hermes env:" in result.output
    assert "Would write Hermes config:" in result.output
    assert "Configured Hermes model: test-model (custom)" in result.output
    assert "test-key" not in result.output
    assert "Hermes setup completed." in result.output


def test_setup_hermes_help_lists_webui_options():
    result = CliRunner().invoke(cli, ["setup", "hermes", "--help"])

    assert result.exit_code == 0
    assert "Setup Hermes Agent and optional Hermes WebUI." in result.output
    assert "--start-webui" in result.output
    assert "--feishu-env" in result.output
