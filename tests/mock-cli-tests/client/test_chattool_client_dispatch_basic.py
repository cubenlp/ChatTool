from __future__ import annotations

from unittest.mock import Mock

import click
import pytest

import chattool.client.main as client_main


pytestmark = pytest.mark.mock_cli


def _make_command(name: str, help_text: str) -> click.Command:
    @click.command(name=name, help=help_text)
    def _cmd():
        pass

    return _cmd


def _make_group(name: str, help_text: str) -> click.Group:
    @click.group(name=name, help=help_text)
    def _group():
        pass

    return _group


def test_main_help_lists_lazy_commands_without_loading_them(runner, monkeypatch):
    load_attr = Mock(
        side_effect=AssertionError("_load_attr should not run for root help")
    )
    monkeypatch.setattr(client_main, "_load_attr", load_attr)

    result = runner.invoke(client_main.cli, ["--help"])

    assert result.exit_code == 0
    assert "dns" not in result.output
    assert "client" in result.output
    assert "skill" in result.output
    load_attr.assert_not_called()


def test_dns_command_is_removed_from_chattool(runner):
    result = runner.invoke(client_main.cli, ["dns", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_client_subcommand_loads_nested_command_on_demand(runner, monkeypatch):
    cert_command = _make_command("cert", "Mock cert client command.")
    load_attr = Mock(return_value=cert_command)
    monkeypatch.setattr(client_main, "_load_attr", load_attr)

    result = runner.invoke(client_main.cli, ["client", "cert", "--help"])

    assert result.exit_code == 0
    assert "Mock cert client command." in result.output
    load_attr.assert_called_once_with("chattool.client.cert_client", "cert_client")
