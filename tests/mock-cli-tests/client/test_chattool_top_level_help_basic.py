import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_top_level_help_entries(runner):
    result = runner.invoke(cli, ["client", "--help"])
    assert result.exit_code == 0
    assert "Manage certificates through the remote cert service." in result.output
    assert "Convert SVG to GIF through the remote svg2gif service." in result.output

    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "Run the screenshot capture server." in result.output
    assert "Run the certificate service." in result.output
    assert "Run the Lark webhook service." in result.output
    assert "Serve a local directory or HTML file." in result.output
    assert "Run the SVG-to-GIF conversion service." in result.output

    result = runner.invoke(cli, ["skill", "--help"])
    assert result.exit_code == 0
    assert "Install one or more skills" in result.output
    assert "List available skills" in result.output

    result = runner.invoke(cli, ["explore", "--help"])
    assert result.exit_code == 0
    assert "currently focused on arXiv" in result.output
    assert "github, wordpress" not in result.output


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


def test_chattool_serve_local_rejects_missing_html(runner, tmp_path):
    result = runner.invoke(cli, ["serve", "local", str(tmp_path), "--dry-run"])

    assert result.exit_code != 0
    assert "HTML file does not exist" in result.output
