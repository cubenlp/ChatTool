from pathlib import Path

import pytest

from chattool import __version__
from chattool.client.main import cli, render_command_tree


pytestmark = pytest.mark.mock_cli


def test_chattool_version_option(runner):
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert f"chattool, version {__version__}" in result.output


def test_chattool_tree_is_generated_from_lazy_registry_without_loading_modules(runner, monkeypatch):
    def fail_load_attr(module_path: str, attr: str):
        raise AssertionError("--tree should use LazyGroup registry metadata without loading modules")

    monkeypatch.setattr("chattool.client.main._load_attr", fail_load_attr)

    result = runner.invoke(cli, ["--tree"])

    assert result.exit_code == 0
    assert result.output == render_command_tree(cli, "chattool") + "\n"
    assert result.output.startswith("chattool  # Unified entry point")
    assert "├── --help  # Show help for the current command." in result.output
    assert "├── --version  # Show package version." in result.output
    assert "├── --tree  # Print the registered CLI tree." in result.output
    assert "browser" in result.output
    assert "serve" in result.output
    assert "skill" in result.output
    assert "\n├── gh" not in result.output
    assert "\n├── image" not in result.output
    assert "\n├── dns" not in result.output


def test_cli_tree_contract_is_documented():
    tree = render_command_tree(cli, "chattool")
    root = Path(__file__).resolve().parents[3]
    assert tree in (root / "README.md").read_text(encoding="utf-8")
    assert tree in (root / "README_en.md").read_text(encoding="utf-8")
    assert tree in (root / "docs" / "cli-tree.md").read_text(encoding="utf-8")
