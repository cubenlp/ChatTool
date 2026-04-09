import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from chattool.setup.cli import setup_group, chrome_cmd, frp_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_setup_group():
    """Test setup group command exists."""
    assert setup_group.name == "setup"


def test_chrome_cmd(runner):
    """Test chrome setup command."""
    with patch("chattool.setup.chrome.setup_chrome_driver") as mock_setup:
        mock_setup.return_value = None
        result = runner.invoke(chrome_cmd, [])
        # Should call the setup function
        mock_setup.assert_called_once()


def test_chrome_cmd_interactive(runner):
    """Test chrome setup command with interactive flag."""
    with patch("chattool.setup.chrome.setup_chrome_driver") as mock_setup:
        mock_setup.return_value = None
        result = runner.invoke(chrome_cmd, ["--interactive"])
        mock_setup.assert_called_once_with(interactive=True)


def test_frp_cmd(runner):
    """Test frp setup command."""
    with patch("chattool.setup.frp.setup_frp") as mock_setup:
        mock_setup.return_value = None
        result = runner.invoke(frp_cmd, [])
        mock_setup.assert_called_once()
