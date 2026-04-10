import sys

import pytest

import chattool.client as client_entry


pytestmark = pytest.mark.mock_cli


def test_chatpypi_name_shortcut_routes_to_init(monkeypatch):
    calls = {}

    class FakeCli:
        def main(self, args=None, prog_name=None):
            calls["args"] = args
            calls["prog_name"] = prog_name

    monkeypatch.setattr(sys, "argv", ["chatpypi", "mypkg"])
    monkeypatch.setattr("chattool.client.main.cli", FakeCli())

    client_entry.main_pypi_cli()

    assert calls == {"args": ["pypi", "init", "mypkg"], "prog_name": "chatpypi"}


def test_chatpypi_explicit_command_passthrough(monkeypatch):
    calls = {}

    class FakeCli:
        def main(self, args=None, prog_name=None):
            calls["args"] = args
            calls["prog_name"] = prog_name

    monkeypatch.setattr(sys, "argv", ["chatpypi", "build"])
    monkeypatch.setattr("chattool.client.main.cli", FakeCli())

    client_entry.main_pypi_cli()

    assert calls == {"args": ["pypi", "build"], "prog_name": "chatpypi"}
