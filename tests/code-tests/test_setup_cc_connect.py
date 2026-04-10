from click.testing import CliRunner

from chattool.client.main import cli as root_cli
from chattool.tools.cc.cli import cli as cc_cli


def test_setup_cc_connect_command_invokes_shared_setup(monkeypatch):
    calls = []
    runner = CliRunner()

    monkeypatch.setattr(
        "chattool.setup.elements.setup_cc_connect",
        lambda interactive=None: calls.append(interactive),
    )

    result = runner.invoke(root_cli, ["setup", "cc-connect", "-i"])

    assert result.exit_code == 0
    assert calls == [True]


def test_cc_setup_alias_invokes_shared_setup(monkeypatch):
    calls = []
    runner = CliRunner()

    monkeypatch.setattr(
        "chattool.setup.cc_connect.setup_cc_connect",
        lambda interactive=None: calls.append(interactive),
    )

    result = runner.invoke(cc_cli, ["setup", "-I"])

    assert result.exit_code == 0
    assert calls == [False]
