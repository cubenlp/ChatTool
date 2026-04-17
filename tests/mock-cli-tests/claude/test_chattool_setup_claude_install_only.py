from click.testing import CliRunner

from chattool.client.main import cli


def test_setup_claude_install_only_does_not_write_config(tmp_path, monkeypatch):
    runner = CliRunner()
    home_dir = tmp_path / "home"

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    import chattool.setup.nodejs as nodejs_setup

    monkeypatch.setattr(
        nodejs_setup,
        "ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        nodejs_setup,
        "should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(cli, ["setup", "claude", "--install-only", "-I"])

    assert result.exit_code == 0
    assert not (home_dir / ".claude" / "settings.json").exists()
    assert not (home_dir / ".claude" / "config.json").exists()
