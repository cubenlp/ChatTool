from pathlib import Path

from chattool.setup.alias import (
    ALIAS_MAP,
    BLOCK_BEGIN,
    BLOCK_END,
    apply_alias_block,
    render_alias_block,
    resolve_shell,
    resolve_shell_rc,
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
    keys = ["chatenv", "chatdns"]
    block = render_alias_block(keys)
    assert BLOCK_BEGIN in block
    assert BLOCK_END in block
    assert "alias chatenv='chattool env'" in block
    assert "alias chatdns='chattool dns'" in block


def test_apply_alias_block_replace(tmp_path):
    rc = tmp_path / ".zshrc"
    rc.write_text("export PATH=/usr/bin\n", encoding="utf-8")
    first = render_alias_block(["chat"])
    apply_alias_block(rc, first)
    content = rc.read_text(encoding="utf-8")
    assert "alias chat='chattool'" in content

    second = render_alias_block(["chatskills"])
    apply_alias_block(rc, second)
    content = rc.read_text(encoding="utf-8")
    assert "alias chat='chattool'" not in content
    assert "alias chatskills='chattool skills'" in content


def test_apply_alias_block_remove(tmp_path):
    rc = tmp_path / ".bashrc"
    rc.write_text("line1\nline2\n", encoding="utf-8")
    apply_alias_block(rc, render_alias_block(list(ALIAS_MAP.keys())))
    apply_alias_block(rc, "")
    content = rc.read_text(encoding="utf-8")
    assert BLOCK_BEGIN not in content
    assert BLOCK_END not in content
