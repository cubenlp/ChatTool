import click
import pytest

from pathlib import Path

from chattool.setup.nodejs import (
    NVM_INIT_BEGIN,
    NVM_INIT_END,
    _install_bundled_nvm,
    _parse_node_major,
    _detect_nodejs_runtime,
    _render_nvm_init_block,
    _replace_managed_block,
    ensure_nodejs_requirement,
    has_required_nodejs,
    run_npm_command,
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

    _replace_managed_block(
        rc_path, NVM_INIT_BEGIN, NVM_INIT_END, _render_nvm_init_block()
    )

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

    _install_bundled_nvm(nvm_sh, [("zsh", shell_rc)])

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

    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime", lambda: next(detections)
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs.has_required_nodejs",
        lambda min_major=20, runtime=None: next(checks),
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs.ask_confirm", lambda message, default=True: True
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs.setup_nodejs",
        lambda interactive=None, log_level="INFO": install_calls.append(
            (interactive, log_level)
        ),
    )

    runtime = ensure_nodejs_requirement(interactive=None, can_prompt=True)

    assert runtime == runtime_ready
    assert install_calls == [(True, "INFO")]


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
    monkeypatch.setattr(
        "chattool.setup.nodejs.has_required_nodejs",
        lambda min_major=20, runtime=None: False,
    )

    with pytest.raises(click.Abort):
        ensure_nodejs_requirement(interactive=False, can_prompt=False)


def test_detect_nodejs_runtime_falls_back_to_nvm(monkeypatch, tmp_path):
    nvm_sh = tmp_path / ".nvm" / "nvm.sh"
    nvm_sh.parent.mkdir(parents=True, exist_ok=True)
    nvm_sh.write_text("# nvm\n", encoding="utf-8")

    monkeypatch.setattr("chattool.setup.nodejs.Path.home", lambda: tmp_path)
    monkeypatch.setattr("chattool.setup.nodejs.shutil.which", lambda name: None)

    def fake_bash_output(command):
        mapping = {
            'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && command -v node': "/fake/.nvm/node",
            'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && command -v npm': "/fake/.nvm/npm",
            'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node -v': "v24.1.0",
            'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && npm -v': "11.1.0",
        }
        return mapping.get(command, "")

    monkeypatch.setattr("chattool.setup.nodejs._get_bash_output", fake_bash_output)

    runtime = _detect_nodejs_runtime()

    assert runtime["source"] == "nvm"
    assert runtime["node_version"] == "v24.1.0"
    assert runtime["npm_version"] == "11.1.0"
    assert runtime["node_major"] == 24


def test_run_npm_command_uses_nvm_when_runtime_comes_from_nvm(monkeypatch, capsys):
    commands = []

    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime",
        lambda: {
            "node_bin": "/fake/.nvm/node",
            "npm_bin": "/fake/.nvm/npm",
            "node_version": "v24.1.0",
            "npm_version": "11.1.0",
            "node_major": 24,
            "source": "nvm",
        },
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs._run_bash",
        lambda command: commands.append(command)
        or type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    result = run_npm_command(["install", "-g", "@openai/codex@latest"])

    assert result.returncode == 0
    assert len(commands) == 1
    assert "npm install -g @openai/codex@latest" in commands[0]
    out = capsys.readouterr().out
    assert "Running: npm install -g @openai/codex@latest" in out


def test_run_npm_command_with_cwd_uses_nvm_shell(monkeypatch, tmp_path):
    commands = []

    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime",
        lambda: {
            "node_bin": "/fake/.nvm/node",
            "npm_bin": "/fake/.nvm/npm",
            "node_version": "v24.1.0",
            "npm_version": "11.1.0",
            "node_major": 24,
            "source": "nvm",
        },
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs._run_bash",
        lambda command: commands.append(command)
        or type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    result = run_npm_command(["install", "--omit=dev"], cwd=tmp_path / "plugin")

    assert result.returncode == 0
    assert len(commands) == 1
    assert f"cd {tmp_path / 'plugin'} && npm install --omit=dev" in commands[0]
