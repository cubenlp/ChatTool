import pytest
from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_hermes_existing_home_config_first_patches_keys(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    hermes_home = home_dir / ".hermes"
    hermes_home.mkdir(parents=True)
    (hermes_home / ".env").write_text(
        "\n".join(
            [
                "# keep comment",
                "OPENAI_API_KEY=sk-existing",
                "CUSTOM_VALUE=keep-me",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (hermes_home / "config.yaml").write_text(
        "\n".join(
            [
                "model:",
                "  default: 'old-model'",
                "  provider: 'openai'",
                "  base_url: 'https://old.example/v1'",
                "custom:",
                "  keep: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(
        "chattool.setup.hermes._run_installer",
        lambda *args, **kwargs: pytest.fail("installer should not run for existing HERMES_HOME"),
    )

    result = CliRunner().invoke(
        cli,
        [
            "setup",
            "hermes",
            "--hermes-home",
            str(hermes_home),
            "--api-key",
            "test-key",
            "--base-url",
            "http://example.test/v1",
            "--model",
            "test-model",
            "--with-webui-env",
            "-I",
        ],
    )

    assert result.exit_code == 0
    env_text = (hermes_home / ".env").read_text(encoding="utf-8")
    config_text = (hermes_home / "config.yaml").read_text(encoding="utf-8")
    assert "# keep comment" in env_text
    assert "CUSTOM_VALUE=keep-me" in env_text
    assert "OPENAI_API_KEY=test-key" in env_text
    assert "custom:" in config_text
    assert "keep: true" in config_text
    assert "default: 'test-model'" in config_text
    assert "base_url: 'http://example.test/v1'" in config_text
    assert "Configured Hermes model: test-model (custom)" in result.output
    assert "test-key" not in result.output
    assert "WebUI env:" in result.output
    assert "Hermes setup completed." in result.output


def test_setup_hermes_install_only_does_not_write_config(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    hermes_home = home_dir / ".hermes"

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("chattool.setup.hermes._hermes_installed", lambda _home: False)
    monkeypatch.setattr(
        "chattool.setup.hermes._run_installer",
        lambda *args, **kwargs: hermes_home.mkdir(parents=True, exist_ok=True),
    )

    result = CliRunner().invoke(
        cli,
        [
            "setup",
            "hermes",
            "--hermes-home",
            str(hermes_home),
            "--install-only",
            "-I",
        ],
    )

    assert result.exit_code == 0
    assert "Hermes install-only completed." in result.output
    assert not (hermes_home / ".env").exists()
    assert not (hermes_home / "config.yaml").exists()


def test_setup_hermes_help_lists_webui_options():
    result = CliRunner().invoke(cli, ["setup", "hermes", "--help"])

    assert result.exit_code == 0
    assert "Setup Hermes Agent and optional Hermes WebUI." in result.output
    assert "--installer" in result.output
    assert "--update-installer" in result.output
    assert "--hermes-home" in result.output
    assert "--with-webui-env" in result.output
    assert "--start-webui" in result.output
    assert "--feishu-env" in result.output
    assert "--dry-run" not in result.output
    assert "--agent-dir" not in result.output
