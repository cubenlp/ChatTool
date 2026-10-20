from pathlib import Path

import click
import pytest

import chattool.config as config
import chattool.config.elements as elements
from chattool.client.main import cli, render_command_tree


pytestmark = pytest.mark.mock_cli


def test_crs_is_no_longer_a_parent_command(runner):
    result = runner.invoke(cli, ["crs", "--help"])
    assert result.exit_code == 2
    assert "No such command" in result.output
    assert cli.get_command(click.Context(cli), "crs") is None
    assert not any(line.startswith(("├── crs", "└── crs")) for line in render_command_tree(cli).splitlines())


def test_crs_config_is_not_registered_or_exported_by_chattool():
    assert not hasattr(config, "CRSConfig")
    assert not hasattr(elements, "CRSConfig")
    owned = [cls for cls in config.BaseEnvConfig._registry if cls.__module__.startswith("chattool.")]
    assert all("crs" not in cls._aliases for cls in owned)


def test_parent_crs_modules_are_removed_and_oauth_helper_is_service_owned():
    root = Path(__file__).resolve().parents[3]
    assert not list((root / "src/chattool/tools/crs").glob("*.py"))
    assert not (root / "src/chattool/config/crs.py").exists()
    from chattool.serve.openai_oauth import build_openai_oauth_status

    assert callable(build_openai_oauth_status)
