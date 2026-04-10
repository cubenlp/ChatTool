import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_nginx_help_and_list(runner):
    result = runner.invoke(cli, ["nginx", "--help"])
    assert result.exit_code == 0
    assert "--list" in result.output
    assert "--set" in result.output

    result = runner.invoke(cli, ["nginx", "--list"])
    assert result.exit_code == 0
    assert "proxy-pass:" in result.output
    assert "proxy-pass-https:" in result.output
    assert "websocket-proxy:" in result.output
    assert "static-root:" in result.output
    assert "redirect:" in result.output


def test_chattool_nginx_requires_template_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["nginx", "-I"])

    assert result.exit_code != 0
    assert "Missing required argument: template" in result.output
    assert "Usage: chattool nginx" in result.output
