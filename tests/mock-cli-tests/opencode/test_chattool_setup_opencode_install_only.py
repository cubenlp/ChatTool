from click.testing import CliRunner

from chattool.client.main import cli


def test_setup_opencode_install_only_does_not_write_config(tmp_path, monkeypatch):
    runner = CliRunner()
    home_dir = tmp_path / "home"

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(cli, ["setup", "opencode", "--install-only", "-I"])

    assert result.exit_code == 0
    assert not (home_dir / ".config" / "opencode" / "opencode.json").exists()
