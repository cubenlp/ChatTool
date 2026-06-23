from pathlib import Path

from chattool.setup.alias import (
    ALIAS_MAP,
    BLOCK_BEGIN,
    BLOCK_END,
    apply_alias_block,
    render_alias_block,
    resolve_shell,
    resolve_shell_rc,
    select_aliases_interactively,
    setup_alias,
)


def test_resolve_shell_with_env(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    assert resolve_shell(None) == "zsh"
    monkeypatch.setenv("SHELL", "/bin/bash")
    assert resolve_shell(None) == "bash"


def test_resolve_shell_rc():
    home = Path("/tmp/demo-home")
    assert resolve_shell_rc("zsh", home=home) == home / ".zshrc"
    assert resolve_shell_rc("bash", home=home) == home / ".bashrc"


def test_render_alias_block():
    keys = ["chatdns"]
    block = render_alias_block(keys)
    assert BLOCK_BEGIN in block
    assert BLOCK_END in block
    assert "alias chatdns='chattool dns'" in block


def test_apply_alias_block_replace(tmp_path):
    rc = tmp_path / ".zshrc"
    rc.write_text("export PATH=/usr/bin\n", encoding="utf-8")
    assert "chatgh" not in ALIAS_MAP
    assert "chatpypi" not in ALIAS_MAP
    assert "chatskill" not in ALIAS_MAP

    first = render_alias_block(["chatdns"])
    apply_alias_block(rc, first)
    content = rc.read_text(encoding="utf-8")
    assert "alias chatdns='chattool dns'" in content

    second = render_alias_block(["chatcc"])
    apply_alias_block(rc, second)
    content = rc.read_text(encoding="utf-8")
    assert "alias chatdns='chattool dns'" not in content
    assert "alias chatcc='chattool cc'" in content


def test_apply_alias_block_remove(tmp_path):
    rc = tmp_path / ".bashrc"
    rc.write_text("line1\nline2\n", encoding="utf-8")
    apply_alias_block(rc, render_alias_block(list(ALIAS_MAP.keys())))
    apply_alias_block(rc, "")
    content = rc.read_text(encoding="utf-8")
    assert BLOCK_BEGIN not in content
    assert BLOCK_END not in content


def test_setup_alias_dry_run_does_not_write(tmp_path, monkeypatch, capsys):
    rc = tmp_path / ".zshrc"
    rc.write_text("export A=1\n", encoding="utf-8")
    monkeypatch.setattr("chattool.setup.alias.resolve_shell_rc", lambda shell: rc)
    monkeypatch.setattr("chattool.setup.alias.is_interactive_available", lambda: False)
    setup_alias(shell="zsh", dry_run=True)
    content = rc.read_text(encoding="utf-8")
    assert content == "export A=1\n"
    out = capsys.readouterr().out
    assert "[dry-run] target shell rc:" in out


def test_select_aliases_interactively_custom_uses_checkbox(monkeypatch):
    captured = {}

    def fake_ask_checkbox_with_controls(
        message,
        choices,
        default_values=None,
        style=None,
        instruction=None,
        select_all_label=None,
    ):
        captured["message"] = message
        captured["choices"] = choices
        captured["default_values"] = default_values
        captured["instruction"] = instruction
        captured["select_all_label"] = select_all_label
        return ["chatdns"]

    monkeypatch.setattr(
        "chattool.setup.alias.ask_checkbox_with_controls",
        fake_ask_checkbox_with_controls,
    )
    selected = select_aliases_interactively(["chatdns"])

    assert selected == ["chatdns"]
    assert captured["message"] == "Select aliases"
    assert captured["default_values"] == ["chatdns"]
    assert captured["select_all_label"] == "Select all aliases"
    def _choice_value(choice):
        return choice.get("value") if isinstance(choice, dict) else choice.value

    def _choice_checked(choice):
        return choice.get("checked") if isinstance(choice, dict) else choice.checked

    checked = {
        _choice_value(choice): _choice_checked(choice)
        for choice in captured["choices"]
    }
    assert "chatgh" not in checked
    assert "chatpypi" not in checked
    assert "chatskill" not in checked
    assert checked["chatdns"] is True
