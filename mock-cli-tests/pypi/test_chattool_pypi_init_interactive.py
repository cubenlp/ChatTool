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
        "template": "default",
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
    monkeypatch.setattr(
        "chattool.tools.pypi.cli.ask_select",
        lambda message, choices, style=None: "default - minimal Python package",
    )

    result = runner.invoke(cli, ["pypi", "init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Package name is required" not in result.output
    assert (tmp_path / "demo-pkg" / "pyproject.toml").exists()


def test_chattool_pypi_init_errors_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["pypi", "init", "-I"])

    assert result.exit_code != 0
    assert "Package name is required" in result.output


def test_chattool_pypi_init_cli_style_template_interactive(
    tmp_path, monkeypatch, runner
):
    answers = {
        "package_name": "demo-pkg",
        "project_dir": str(tmp_path / "demo-pkg"),
        "description": "demo-pkg package",
        "version": "0.1.0",
        "requires_python": ">=3.9",
        "license": "MIT",
        "author": "",
        "email": "",
        "template": "cli-style",
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
    monkeypatch.setattr(
        "chattool.tools.pypi.cli.ask_select",
        lambda message,
        choices,
        style=None: "cli-style - CLI/docs/tests/automation scaffold with chatstyle",
    )

    result = runner.invoke(cli, ["pypi", "init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (tmp_path / "demo-pkg" / "DEVELOP.md").exists()
    assert (tmp_path / "demo-pkg" / "setup.md").exists()
    assert (tmp_path / "demo-pkg" / ".github" / "workflows" / "ci.yml").exists()


def test_chattool_pypi_init_stops_early_when_project_dir_not_empty(
    tmp_path, monkeypatch, runner
):
    occupied = tmp_path / "demo-pkg"
    occupied.mkdir()
    (occupied / "existing.txt").write_text("busy", encoding="utf-8")

    prompts = []
    answers = {
        "package_name": "demo-pkg",
        "project_dir": str(occupied),
    }

    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.tools.pypi.cli.ask_select",
        lambda message, choices, style=None: "default - minimal Python package",
    )

    def fake_ask_text(label, default="", password=False, style=None):
        prompts.append(label)
        return answers[label]

    monkeypatch.setattr("chattool.tools.pypi.cli.ask_text", fake_ask_text)

    result = runner.invoke(cli, ["pypi", "init"])

    assert result.exit_code != 0
    assert f"Target directory is not empty: {occupied}" in result.output
    assert prompts == ["package_name", "project_dir"]
