from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_client_svg2gif_prompts_for_missing_svg(runner, monkeypatch):
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_path",
        lambda message, default="", style=None: "/tmp/demo.svg",
    )

    post_mock = Mock()
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "gif_path": "/tmp/demo.gif",
        "frames": 10,
        "duration_ms": 2000,
    }
    post_mock.return_value = response
    monkeypatch.setattr("requests.post", post_mock)

    result = runner.invoke(cli, ["client", "svg2gif"], catch_exceptions=False)

    assert result.exit_code == 0
    post_mock.assert_called_once()
    assert post_mock.call_args.kwargs["json"]["svg_path"] == "/tmp/demo.svg"


def test_client_svg2gif_errors_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["client", "svg2gif", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: svg_path" in result.output


def test_client_cert_apply_prompts_for_missing_values(runner, monkeypatch):
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )

    answers = {
        "域名": "example.com",
        "Let's Encrypt 邮箱": "admin@example.com",
        "DNS 提供商": "aliyun",
        "云厂商 Secret ID": "",
        "云厂商 Secret Key": "",
    }

    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_select",
        lambda message, choices, style=None: answers[message],
    )

    post_mock = Mock()
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "queued", "message": "submitted"}
    post_mock.return_value = response
    monkeypatch.setattr("requests.post", post_mock)

    result = runner.invoke(cli, ["client", "cert", "apply"], catch_exceptions=False)

    assert result.exit_code == 0
    payload = post_mock.call_args.kwargs["json"]
    assert payload["domains"] == ["example.com"]
    assert payload["email"] == "admin@example.com"
    assert payload["provider"] == "aliyun"


def test_client_cert_download_prompts_for_domain(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "example.com",
    )

    response = Mock(status_code=404)
    get_mock = Mock(return_value=response)
    monkeypatch.setattr("requests.get", get_mock)

    result = runner.invoke(
        cli,
        ["client", "cert", "download", "-o", str(tmp_path)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    first_url = get_mock.call_args_list[0].args[0]
    assert "/cert/download/example.com/cert.pem" in first_url
