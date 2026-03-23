import pathlib
from types import SimpleNamespace
import subprocess

import chattool.setup.claude as claude_module
import chattool.setup.codex as codex_module
import chattool.setup.opencode as opencode_module


def test_setup_codex_checks_nodejs_before_prompts_and_uses_new_default_model(tmp_path, monkeypatch):
    events = []
    prompts = []

    monkeypatch.setattr(codex_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        codex_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(
        codex_module,
        "ensure_nodejs_requirement",
        lambda interactive=None, can_prompt=False: events.append(("nodejs", interactive, can_prompt)),
    )

    def fake_ask_text(message, default="", password=False):
        events.append(("prompt", message))
        prompts.append((message, default, password))
        if "preferred_auth_method" in message:
            return "cr_test_token"
        return default

    monkeypatch.setattr(codex_module, "ask_text", fake_ask_text)
    monkeypatch.setattr(
        codex_module.subprocess,
        "run",
        lambda cmd, capture_output=True, text=True: SimpleNamespace(returncode=0, stderr="", stdout=""),
    )

    codex_module.setup_codex(interactive=None)

    assert events[0] == ("nodejs", None, True)
    assert prompts[1] == ("base_url (optional)", "https://api.openai.com/v1", False)
    assert prompts[2] == ("default model (optional)", "gpt-5.4", False)
    config_text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert 'model = "gpt-5.4"' in config_text


def test_setup_claude_checks_nodejs_before_prompts_and_uses_new_default_model(tmp_path, monkeypatch):
    events = []
    prompts = []

    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        "chattool.setup.interactive.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs.ensure_nodejs_requirement",
        lambda interactive=None, can_prompt=False: events.append(("nodejs", interactive, can_prompt)),
    )

    def fake_ask_text(message, default="", password=False):
        events.append(("prompt", message))
        prompts.append((message, default, password))
        if message == "ANTHROPIC_AUTH_TOKEN":
            return "sk-ant-test"
        return default

    monkeypatch.setattr("chattool.utils.tui.ask_text", fake_ask_text)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, capture_output=True, text=True: SimpleNamespace(returncode=0, stderr="", stdout=""),
    )

    claude_module.setup_claude(interactive=None)

    assert events[0] == ("nodejs", None, True)
    assert prompts[1] == ("ANTHROPIC_BASE_URL (optional)", claude_module.DEFAULT_BASE_URL, False)
    assert prompts[2] == ("ANTHROPIC_SMALL_FAST_MODEL (optional)", "claude-opus-4-6", False)
    settings_text = (tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert '"ANTHROPIC_SMALL_FAST_MODEL": "claude-opus-4-6"' in settings_text


def test_setup_opencode_checks_nodejs_before_prompts(tmp_path, monkeypatch):
    events = []

    monkeypatch.setattr(opencode_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        opencode_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(
        opencode_module,
        "ensure_nodejs_requirement",
        lambda interactive=None, can_prompt=False: events.append(("nodejs", interactive, can_prompt)),
    )

    def fake_ask_text(message, default="", password=False):
        events.append(("prompt", message))
        values = {
            "base_url": "https://example.com/openai",
            "api_key": "sk-test",
            "model": "gpt-4.1-mini",
        }
        return values[message]

    monkeypatch.setattr(opencode_module, "ask_text", fake_ask_text)
    monkeypatch.setattr(
        opencode_module.subprocess,
        "run",
        lambda cmd, capture_output=True, text=True: SimpleNamespace(returncode=0, stderr="", stdout=""),
    )

    opencode_module.setup_opencode(interactive=None)

    assert events[0] == ("nodejs", None, True)
    assert events[1:] == [("prompt", "base_url"), ("prompt", "api_key"), ("prompt", "model")]
    config_text = (tmp_path / ".config" / "opencode" / "opencode.json").read_text(encoding="utf-8")
    assert '"model": "opencode/gpt-4.1-mini"' in config_text
