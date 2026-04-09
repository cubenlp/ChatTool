import subprocess

import pytest

from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_nodejs_updates_all_detected_shell_rc_files(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "chattool.setup.alias.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"zsh", "bash"} else None,
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs._detect_nodejs_runtime",
        lambda: {
            "node_bin": "",
            "npm_bin": "",
            "node_version": "",
            "npm_version": "",
            "node_major": None,
            "source": "path",
        },
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs.has_required_nodejs", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs._read_bundled_nvm_script",
        lambda: "# mock bundled nvm\n",
    )
    monkeypatch.setattr(
        "chattool.setup.nodejs._run_bash_with_output_tail",
        lambda command: subprocess.CompletedProcess(command, 0, "", ""),
    )

    def _fake_bash_output(command):
        if "node -v" in command:
            return "v22.1.0"
        if "npm -v" in command:
            return "10.8.0"
        return ""

    monkeypatch.setattr("chattool.setup.nodejs._get_bash_output", _fake_bash_output)

    result = CliRunner().invoke(cli, ["setup", "nodejs"])

    assert result.exit_code == 0
    assert "Node.js version: v22.1.0" in result.output
    assert "npm version: 10.8.0" in result.output

    nvm_sh = tmp_path / ".nvm" / "nvm.sh"
    zshrc = tmp_path / ".zshrc"
    bashrc = tmp_path / ".bashrc"

    assert nvm_sh.exists()
    assert zshrc.exists()
    assert bashrc.exists()

    zsh_content = zshrc.read_text(encoding="utf-8")
    bash_content = bashrc.read_text(encoding="utf-8")
    assert "# >>> chattool nvm >>>" in zsh_content
    assert 'export NVM_DIR="$HOME/.nvm"' in zsh_content
    assert "# >>> chattool nvm >>>" in bash_content
    assert 'export NVM_DIR="$HOME/.nvm"' in bash_content


def test_setup_nodejs_accepts_log_level_option(monkeypatch):
    captured = {}

    def fake_setup_logger(name, log_level="INFO", **kwargs):
        captured["name"] = name
        captured["log_level"] = log_level

        class DummyLogger:
            def info(self, *_args, **_kwargs):
                pass

            def warning(self, *_args, **_kwargs):
                pass

            def error(self, *_args, **_kwargs):
                pass

        return DummyLogger()

    monkeypatch.setattr("chattool.setup.nodejs.setup_logger", fake_setup_logger)
    monkeypatch.setattr(
        "chattool.setup.nodejs.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (_ for _ in ()).throw(SystemExit(0)),
    )

    result = CliRunner().invoke(cli, ["setup", "nodejs", "--log-level", "DEBUG", "-I"])

    assert result.exit_code == 0
    assert captured["name"] == "setup_nodejs"
    assert captured["log_level"] == "DEBUG"
