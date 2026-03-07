import json
import pytest
from click.testing import CliRunner

from chattool.cli.client import mcp as mcp_cli


class DummyMCP:
    def __init__(self, include_tags=None, exclude_tags=None):
        self.name = "Dummy MCP"
        self.include_tags = include_tags or set()
        self.exclude_tags = exclude_tags or set()

    def run(self, **kwargs):
        return kwargs


def test_mcp_info_json(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(mcp_cli, "mcp", DummyMCP())
    result = runner.invoke(mcp_cli.cli, ["info", "--json-output"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["name"] == "Dummy MCP"
    assert payload["tool_count"] >= 10
    names = {item["name"] for item in payload["tools"]}
    assert "dns_list_domains" in names
    assert "zulip_send_message" in names
    assert "network_ping_scan" in names


def test_mcp_inspect_alias(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(mcp_cli, "mcp", DummyMCP())
    result = runner.invoke(mcp_cli.cli, ["inspect"])
    assert result.exit_code == 0
    assert "MCP Server: Dummy MCP" in result.output
