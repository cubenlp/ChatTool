from pathlib import Path

import pytest
from click.testing import CliRunner

import chattool
from chattool.client.main import cli as chattool_cli
from chattool.serve.cli import serve_cli


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_chattool_no_longer_exports_lark_helpers():
    assert "LarkBot" not in chattool.__all__
    assert not hasattr(chattool, "LarkBot")


def test_chattool_no_longer_exports_feishu_env_schema():
    import chattool.config as config

    assert "FeishuConfig" not in config.__all__
    assert not hasattr(config, "FeishuConfig")


@pytest.mark.parametrize(
    "path",
    [
        "src/chattool/tools/lark",
        "src/chattool/serve/lark_serve.py",
        "src/chattool/config/feishu.py",
    ],
)
def test_embedded_lark_implementation_removed(path):
    assert not (REPO_ROOT / path).exists()


def test_chattool_cli_no_longer_registers_lark_group():
    assert "lark" not in chattool_cli._lazy_commands

    result = CliRunner().invoke(chattool_cli, ["lark", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_chattool_serve_no_longer_registers_lark_group():
    assert "lark" not in serve_cli._lazy_commands

    result = CliRunner().invoke(chattool_cli, ["serve", "lark", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output
