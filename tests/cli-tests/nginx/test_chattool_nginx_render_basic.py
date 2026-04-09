from pathlib import Path

import pytest
from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = [pytest.mark.e2e]


def test_chattool_nginx_basic(tmp_path: Path):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "nginx",
            "proxy-pass",
            "--set",
            "SERVER_NAME=app.example.com",
            "--set",
            "PROXY_PASS=http://127.0.0.1:8080",
        ],
    )
    assert result.exit_code == 0
    assert "server_name app.example.com;" in result.output
    assert "proxy_pass http://127.0.0.1:8080;" in result.output

    ws_file = tmp_path / "websocket.conf"
    result = runner.invoke(
        cli,
        [
            "nginx",
            "websocket-proxy",
            str(ws_file),
            "--set",
            "SERVER_NAME=ws.example.com",
            "--set",
            "PROXY_PASS=http://127.0.0.1:3000",
            "--force",
        ],
    )
    assert result.exit_code == 0
    ws_content = ws_file.read_text(encoding="utf-8")
    assert 'proxy_set_header Connection "upgrade";' in ws_content
    assert "proxy_http_version 1.1;" in ws_content
    assert "proxy_set_header Upgrade $http_upgrade;" in ws_content

    nas_file = tmp_path / "nas.conf"
    result = runner.invoke(
        cli,
        [
            "nginx",
            "static-root",
            str(nas_file),
            "--set",
            "SERVER_NAME=share.example.com",
            "--set",
            "ROOT_DIR=/var/www/example-site",
            "--force",
        ],
    )
    assert result.exit_code == 0
    nas_content = nas_file.read_text(encoding="utf-8")
    assert "root /var/www/example-site;" in nas_content
    assert "autoindex on;" in nas_content
    assert "charset utf-8;" in nas_content

    result = runner.invoke(
        cli,
        [
            "nginx",
            "redirect",
            "--set",
            "SERVER_NAME=example.com www.example.com",
        ],
    )
    assert result.exit_code == 0
    assert "return 301 https://$host$request_uri;" in result.output
