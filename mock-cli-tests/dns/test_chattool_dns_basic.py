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

        result = runner.invoke(cli, ["dns", "ddns"])
        assert result.exit_code != 0
        assert "必须提供" in result.output


def test_dns_get_set_parsing(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []
        client.add_domain_record.return_value = True

        result = runner.invoke(cli, ["dns", "set", "test.example.com", "-v", "1.2.3.4"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["dns", "get", "test.example.com"])
        assert result.exit_code == 0
