import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_serve_oauth_help_and_dry_run(runner, tmp_path):
    help_result = runner.invoke(cli, ["serve", "oauth", "--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "Run the local OAuth token service" in help_result.output
    assert "--token" in help_result.output

    result = runner.invoke(
        cli,
        [
            "serve",
            "oauth",
            "--host",
            "127.0.0.1",
            "--port",
            "8788",
            "--token",
            "service-token-secret",
            "--env-dir",
            str(tmp_path / "envs"),
            "--oauth-base-url",
            "https://oauth.example.test",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "OAuth service: http://127.0.0.1:8788" in result.output
    assert f"Env dir: {tmp_path / 'envs'}" in result.output
    assert "OAuth base: https://oauth.example.test" in result.output
    assert "Service token: configured" in result.output
    assert "service-token-secret" not in result.output


def test_chattool_serve_local_resolves_html_file(runner, tmp_path):
    html_file = tmp_path / "cli-tree.html"
    html_file.write_text("<html></html>\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "serve",
            "local",
            str(html_file),
            "--host",
            "0.0.0.0",
            "--port",
            "9001",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"Root: {tmp_path}" in result.output
    assert f"HTML: {html_file}" in result.output
    assert "URL:  http://0.0.0.0:9001/cli-tree.html" in result.output


def test_chattool_serve_local_resolves_directory_index(runner, tmp_path):
    index_file = tmp_path / "index.html"
    index_file.write_text("<html></html>\n", encoding="utf-8")

    result = runner.invoke(cli, ["serve", "local", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert f"Root: {tmp_path}" in result.output
    assert f"HTML: {index_file}" in result.output
    assert "URL:  http://127.0.0.1:8765/index.html" in result.output


def test_chattool_serve_local_resolves_directory_custom_html(runner, tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    html_file = report_dir / "cli-tree.html"
    html_file.write_text("<html></html>\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        ["serve", "local", str(report_dir), "--html", "cli-tree.html", "--dry-run"],
    )

    assert result.exit_code == 0, result.output
    assert f"Root: {report_dir}" in result.output
    assert f"HTML: {html_file}" in result.output
    assert "URL:  http://127.0.0.1:8765/cli-tree.html" in result.output


def test_chattool_serve_local_prompts_for_target_with_interactive_flag(
    runner, tmp_path, monkeypatch
):
    index_file = tmp_path / "index.html"
    index_file.write_text("<html></html>\n", encoding="utf-8")
    prompted = []

    def fake_ask_path(message, *, default=""):
        prompted.append((message, default))
        return str(tmp_path)

    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr("chattool.interaction.command_schema.ask_path", fake_ask_path)
    result = runner.invoke(cli, ["serve", "local", "-i", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert prompted == [("HTML file or directory", ".")]
    assert f"HTML: {index_file}" in result.output


def test_chattool_serve_local_rejects_missing_html(runner, tmp_path):
    result = runner.invoke(cli, ["serve", "local", str(tmp_path), "--dry-run"])

    assert result.exit_code != 0
    assert "HTML file does not exist" in result.output
