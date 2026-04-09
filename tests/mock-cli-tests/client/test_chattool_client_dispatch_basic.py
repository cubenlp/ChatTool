from __future__ import annotations

from unittest.mock import Mock, call

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
    assert "dns" in result.output
    assert "client" in result.output
    assert "skill" in result.output
    load_attr.assert_not_called()


def test_dns_help_mounts_cert_update_command(runner, monkeypatch):
    dns_group = _make_group("dns", "Mock DNS group.")
    cert_command = _make_command("main", "Mock cert update command.")
    load_attr = Mock(side_effect=[dns_group, cert_command])
    monkeypatch.setattr(client_main, "_load_attr", load_attr)

    result = runner.invoke(client_main.cli, ["dns", "--help"])

    assert result.exit_code == 0
    assert "cert-update" in result.output
    assert "Mock cert update command." in result.output
    assert load_attr.mock_calls == [
        call("chattool.tools.dns.cli", "cli"),
        call("chattool.tools.cert.cli", "main"),
    ]


def test_client_subcommand_loads_nested_command_on_demand(runner, monkeypatch):
    cert_command = _make_command("cert", "Mock cert client command.")
    load_attr = Mock(return_value=cert_command)
    monkeypatch.setattr(client_main, "_load_attr", load_attr)

    result = runner.invoke(client_main.cli, ["client", "cert", "--help"])

    assert result.exit_code == 0
    assert "Mock cert client command." in result.output
    load_attr.assert_called_once_with("chattool.client.cert_client", "cert_client")
