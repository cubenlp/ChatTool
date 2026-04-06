from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_pypi_init_prompts_when_name_missing(tmp_path, monkeypatch, runner):
    answers = {
        "package_name": "demo-pkg",
        "project_dir": str(tmp_path / "demo-pkg"),
        "description": "demo-pkg package",
        "version": "0.1.0",
        "requires_python": ">=3.9",
        "license": "MIT",
        "author": "",
        "email": "",
    }
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.tools.pypi.cli._read_git_config",
        lambda key: {
            "user.name": "RexWzh",
            "user.email": "1073853456@qq.com",
        }.get(key),
    )
    monkeypatch.setattr(
        "chattool.tools.pypi.cli.ask_text",
        lambda label, default="", password=False, style=None: answers[label],
    )

    result = runner.invoke(cli, ["pypi", "init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Package name is required" not in result.output
    assert (tmp_path / "demo-pkg" / "pyproject.toml").exists()


def test_chattool_pypi_init_errors_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["pypi", "init", "-I"])

    assert result.exit_code != 0
    assert "Package name is required" in result.output
