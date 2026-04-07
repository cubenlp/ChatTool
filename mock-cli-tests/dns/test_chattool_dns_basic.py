import pytest
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


@pytest.fixture
def runner():
    return CliRunner()


def test_dns_help_commands(runner):
    result = runner.invoke(cli, ["dns", "get", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "ddns", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "cert-update", "--help"])
    assert result.exit_code == 0


def test_dns_ddns_argument_parsing(runner):
    with patch("chattool.tools.dns.cli.DynamicIPUpdater") as MockUpdater:
        instance = MockUpdater.return_value
        instance.run_once = AsyncMock(return_value=True)

        result = runner.invoke(cli, ["dns", "ddns", "test.rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "test"

        result = runner.invoke(cli, ["dns", "ddns", "rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "@"

        result = runner.invoke(cli, ["dns", "ddns", "a.b.rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "a.b"

        result = runner.invoke(
            cli, ["dns", "ddns", "test.rexwang.site", "-d", "other.com"]
        )
        assert result.exit_code == 0
        assert "警告" in result.output
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"

        result = runner.invoke(cli, ["dns", "ddns", "-d", "example.com", "-r", "www"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "example.com"
        assert call_args["rr"] == "www"

        result = runner.invoke(cli, ["dns", "ddns", "-I"])
        assert result.exit_code != 0
        assert "必须提供" in result.output


def test_dns_root_prompts_for_command_and_runs_set_flow(runner, monkeypatch):
    prompts = iter(["example.com", "www", "1.2.3.4"])

    monkeypatch.setattr("chattool.tools.dns.cli.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.tools.dns.cli.ask_select",
        lambda message, choices, style=None: "set - 创建或更新 DNS 记录",
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: next(prompts),
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []
        client.add_domain_record.return_value = True

        result = runner.invoke(cli, ["dns"], catch_exceptions=False)

    assert result.exit_code == 0
    client.add_domain_record.assert_called_once_with(
        "example.com", "www", "A", "1.2.3.4", 600
    )


def test_dns_set_prompts_when_required_args_missing(runner, monkeypatch):
    answers = {
        "domain": "example.com",
        "rr": "test",
        "value": "1.2.3.4",
    }

    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: answers[label],
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []
        client.add_domain_record.return_value = True

        result = runner.invoke(cli, ["dns", "set"], catch_exceptions=False)

    assert result.exit_code == 0
    client.add_domain_record.assert_called_once_with(
        "example.com", "test", "A", "1.2.3.4", 600
    )


def test_dns_set_errors_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["dns", "set", "-I"])

    assert result.exit_code != 0
    assert "必须提供 full_domain" in result.output


def test_dns_get_prompts_when_domain_missing(runner, monkeypatch):
    answers = {
        "domain": "example.com",
        "rr": "api",
    }

    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: answers[label],
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []

        result = runner.invoke(cli, ["dns", "get"], catch_exceptions=False)

    assert result.exit_code == 0
    client.describe_domain_records.assert_called_once_with(
        "example.com", subdomain="api", record_type=None
    )


def test_dns_get_set_parsing(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []
        client.add_domain_record.return_value = True

        result = runner.invoke(cli, ["dns", "set", "test.example.com", "-v", "1.2.3.4"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["dns", "get", "test.example.com"])
        assert result.exit_code == 0
