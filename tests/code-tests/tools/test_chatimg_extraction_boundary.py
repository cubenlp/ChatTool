from pathlib import Path

from click.testing import CliRunner

import chattool.config as config
from chattool.client.main import cli as chattool_cli


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_chattool_no_longer_registers_image_group():
    assert "image" not in chattool_cli._lazy_commands

    result = CliRunner().invoke(chattool_cli, ["image", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_chattool_no_longer_embeds_image_modules():
    removed_paths = [
        "src/chattool/tools/image",
        "src/chattool/config/tongyi.py",
        "src/chattool/config/huggingface.py",
        "src/chattool/config/pollinations.py",
        "src/chattool/config/liblib.py",
        "src/chattool/config/siliconflow.py",
    ]

    for path in removed_paths:
        assert not (REPO_ROOT / path).exists()


def test_chattool_no_longer_exports_image_provider_env_schemas():
    removed_exports = {
        "TongyiConfig",
        "HuggingFaceConfig",
        "PollinationsConfig",
        "LiblibConfig",
        "SiliconFlowConfig",
    }

    for name in removed_exports:
        assert name not in config.__all__
        assert not hasattr(config, name)
