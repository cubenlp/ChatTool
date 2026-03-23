from pathlib import Path

from chattool.setup.nodejs import (
    NVM_INIT_BEGIN,
    NVM_INIT_END,
    _install_bundled_nvm,
    _render_nvm_init_block,
    _replace_managed_block,
)


def test_render_nvm_init_block():
    block = _render_nvm_init_block()
    assert NVM_INIT_BEGIN in block
    assert NVM_INIT_END in block
    assert 'export NVM_DIR="$HOME/.nvm"' in block
    assert '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' in block


def test_replace_managed_block_updates_existing_block(tmp_path):
    rc_path = tmp_path / ".zshrc"
    rc_path.write_text(
        "\n".join(
            [
                "export PATH=/usr/bin",
                NVM_INIT_BEGIN,
                "old line",
                NVM_INIT_END,
                "",
            ]
        ),
        encoding="utf-8",
    )

    _replace_managed_block(rc_path, NVM_INIT_BEGIN, NVM_INIT_END, _render_nvm_init_block())

    content = rc_path.read_text(encoding="utf-8")
    assert "old line" not in content
    assert content.count(NVM_INIT_BEGIN) == 1
    assert content.count(NVM_INIT_END) == 1


def test_install_bundled_nvm_writes_script_and_shell_init(tmp_path, monkeypatch):
    nvm_sh = tmp_path / ".nvm" / "nvm.sh"
    shell_rc = tmp_path / ".zshrc"
    monkeypatch.setattr(
        "chattool.setup.nodejs._read_bundled_nvm_script",
        lambda: "# bundled nvm\nnvm() { :; }\n",
    )

    _install_bundled_nvm(nvm_sh, shell_rc)

    assert nvm_sh.exists()
    assert nvm_sh.read_text(encoding="utf-8") == "# bundled nvm\nnvm() { :; }\n"
    assert nvm_sh.stat().st_mode & 0o111

    shell_content = shell_rc.read_text(encoding="utf-8")
    assert NVM_INIT_BEGIN in shell_content
    assert NVM_INIT_END in shell_content
    assert 'export NVM_DIR="$HOME/.nvm"' in shell_content
