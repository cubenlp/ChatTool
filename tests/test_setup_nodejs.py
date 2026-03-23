import click
import pytest

from pathlib import Path

from chattool.setup.nodejs import (
    NVM_INIT_BEGIN,
    NVM_INIT_END,
    _install_bundled_nvm,
    _parse_node_major,
    _render_nvm_init_block,
    _replace_managed_block,
    ensure_nodejs_requirement,
    has_required_nodejs,
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


@pytest.mark.parametrize(
    ("version_text", "expected"),
    [
        ("v20.11.1", 20),
        ("22.4.0", 22),
        ("", None),
        ("not-a-version", None),
    ],
)
def test_parse_node_major(version_text, expected):
    assert _parse_node_major(version_text) == expected


def test_has_required_nodejs_uses_detected_runtime(monkeypatch):
    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime",
        lambda: {
            "node_bin": "/usr/bin/node",
            "npm_bin": "/usr/bin/npm",
            "node_version": "v20.10.0",
            "npm_version": "10.1.0",
            "node_major": 20,
        },
    )

    assert has_required_nodejs() is True


def test_ensure_nodejs_requirement_prompts_install_and_rechecks(monkeypatch):
    runtime_missing = {
        "node_bin": None,
        "npm_bin": None,
        "node_version": "",
        "npm_version": "",
        "node_major": None,
    }
    runtime_ready = {
        "node_bin": "/usr/bin/node",
        "npm_bin": "/usr/bin/npm",
        "node_version": "v20.12.0",
        "npm_version": "10.8.0",
        "node_major": 20,
    }
    detections = iter([runtime_missing, runtime_ready])
    checks = iter([False, True])
    install_calls = []

    monkeypatch.setattr("chattool.setup.nodejs._detect_nodejs_runtime", lambda: next(detections))
    monkeypatch.setattr("chattool.setup.nodejs.has_required_nodejs", lambda min_major=20, runtime=None: next(checks))
    monkeypatch.setattr("chattool.setup.nodejs.ask_confirm", lambda message, default=True: True)
    monkeypatch.setattr(
        "chattool.setup.nodejs.setup_nodejs",
        lambda interactive=None: install_calls.append(interactive),
    )

    runtime = ensure_nodejs_requirement(interactive=None, can_prompt=True)

    assert runtime == runtime_ready
    assert install_calls == [True]


def test_ensure_nodejs_requirement_aborts_without_prompt(monkeypatch):
    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime",
        lambda: {
            "node_bin": None,
            "npm_bin": None,
            "node_version": "",
            "npm_version": "",
            "node_major": None,
        },
    )
    monkeypatch.setattr("chattool.setup.nodejs.has_required_nodejs", lambda min_major=20, runtime=None: False)

    with pytest.raises(click.Abort):
        ensure_nodejs_requirement(interactive=False, can_prompt=False)
