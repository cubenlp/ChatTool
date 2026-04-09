import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_top_level_help_entries(runner):
    result = runner.invoke(cli, ["client", "--help"])
    assert result.exit_code == 0
    assert "Manage certificates through the remote cert service." in result.output
    assert "Convert SVG to GIF through the remote svg2gif service." in result.output

    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "Run the screenshot capture server." in result.output
    assert "Run the certificate service." in result.output
    assert "Run the Lark webhook service." in result.output
    assert "Run the SVG-to-GIF conversion service." in result.output

    result = runner.invoke(cli, ["skill", "--help"])
    assert result.exit_code == 0
    assert "Install one or more skills" in result.output
    assert "List available skills" in result.output

    result = runner.invoke(cli, ["explore", "--help"])
    assert result.exit_code == 0
    assert "currently focused on arXiv" in result.output
    assert "github, wordpress" not in result.output
