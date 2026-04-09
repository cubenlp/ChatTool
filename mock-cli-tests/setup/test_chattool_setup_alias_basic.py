import pytest

from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_alias_uses_shared_multi_select_controls(monkeypatch):
    monkeypatch.setattr("chattool.setup.alias.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.setup.alias.ask_checkbox_with_controls",
        lambda *args, **kwargs: ["chatenv", "chatskill"],
    )

    result = CliRunner().invoke(cli, ["setup", "alias", "--dry-run"])

    assert result.exit_code == 0
    assert "chatenv => chattool env" in result.output
    assert "chatskill => chattool skill" in result.output
    assert "chatdns => chattool dns" not in result.output


def test_setup_alias_detects_all_available_shells_by_default(monkeypatch):
    monkeypatch.setattr("chattool.setup.alias.is_interactive_available", lambda: False)
    monkeypatch.setattr(
        "chattool.setup.alias.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"zsh", "bash"} else None,
    )

    result = CliRunner().invoke(cli, ["setup", "alias", "--dry-run"])

    assert result.exit_code == 0
    assert ".zshrc" in result.output
    assert ".bashrc" in result.output
    assert "chattp => chattool tplogin" in result.output
