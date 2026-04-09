import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_remaining_top_level_help_entries(runner):
    result = runner.invoke(cli, ["dns", "--help"])
    assert result.exit_code == 0
    assert "dynamic IP updates and record management" in result.output

    result = runner.invoke(cli, ["lark", "--help"])
    assert result.exit_code == 0
    assert "Show bot profile info and validate credentials." in result.output
    assert "Send a text message." in result.output

    result = runner.invoke(cli, ["tplogin", "--help"])
    assert result.exit_code == 0
    assert "TP-Link router helpers." in result.output
    assert "Show router device info." in result.output
    assert "ufw-style interface" in result.output

    result = runner.invoke(cli, ["cc", "--help"])
    assert result.exit_code == 0
    assert "cc-connect" in result.output
    assert "doctor" in result.output
    assert "init" in result.output
