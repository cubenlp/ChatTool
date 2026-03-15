from pathlib import Path

from chattool.setup.alias import (
    ALIAS_MAP,
    BLOCK_BEGIN,
    BLOCK_END,
    apply_alias_block,
    render_alias_block,
    resolve_shell,
    resolve_shell_rc,
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
    keys = ["chatenv", "chatdns"]
    block = render_alias_block(keys)
    assert BLOCK_BEGIN in block
    assert BLOCK_END in block
    assert "alias chatenv='chattool env'" in block
    assert "alias chatdns='chattool dns'" in block


def test_apply_alias_block_replace(tmp_path):
    rc = tmp_path / ".zshrc"
    rc.write_text("export PATH=/usr/bin\n", encoding="utf-8")
    first = render_alias_block(["chatgh"])
    apply_alias_block(rc, first)
    content = rc.read_text(encoding="utf-8")
    assert "alias chatgh='chattool gh'" in content

    second = render_alias_block(["chatskills"])
    apply_alias_block(rc, second)
    content = rc.read_text(encoding="utf-8")
    assert "alias chatgh='chattool gh'" not in content
    assert "alias chatskills='chattool skills'" in content


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
    assert "alias chatenv='chattool env'" in out
