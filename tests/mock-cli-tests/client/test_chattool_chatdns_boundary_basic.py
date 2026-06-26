import json
from datetime import datetime, timedelta

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_dns_command_is_removed(runner):
    result = runner.invoke(cli, ["dns", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_certificate_exports_are_backed_by_chatdns():
    import chatdns
    import chattool
    import chattool.tools
    import chattool.tools.cert

    assert chattool.SSLCertUpdater is chatdns.SSLCertUpdater
    assert chattool.tools.SSLCertUpdater is chatdns.SSLCertUpdater
    assert chattool.tools.cert.SSLCertUpdater is chatdns.SSLCertUpdater


def test_cert_server_import_uses_chatdns_updater():
    import chatdns
    import chattool.tools.cert.cert_server as cert_server

    assert cert_server.SSLCertUpdater is chatdns.SSLCertUpdater


def test_serve_cert_help_remains_available_without_starting_server(runner):
    result = runner.invoke(cli, ["serve", "cert", "--help"])

    assert result.exit_code == 0
    assert "启动 SSL 证书服务" in result.output
    assert "--provider" in result.output
    assert "--secret-id" in result.output


@pytest.mark.asyncio
async def test_cert_server_metadata_uses_chatdns_normalized_domain(tmp_path, monkeypatch):
    import chattool.tools.cert.cert_server as cert_server

    class FakeUpdater:
        def __init__(self, domains, email, **kwargs):
            self.domains = [domain.strip().rstrip(".").lower() for domain in domains]
            self.email = email
            self.kwargs = kwargs

        async def run_once(self):
            return True

        def check_cert_expiry(self, domain):
            assert domain == "*.example.com"
            return datetime.now() + timedelta(days=90)

    monkeypatch.setattr(cert_server, "SSLCertUpdater", FakeUpdater)
    monkeypatch.setitem(cert_server.config, "cert_dir", str(tmp_path))
    monkeypatch.setitem(cert_server.config, "provider", "aliyun")
    monkeypatch.setitem(cert_server.config, "secret_id", None)
    monkeypatch.setitem(cert_server.config, "secret_key", None)

    req = cert_server.ApplyRequest(
        domains=["*.Example.COM."],
        email="admin@example.com",
        provider=None,
        secret_id=None,
        secret_key=None,
    )

    await cert_server.run_cert_update_task("token", req)

    token_hash = cert_server.get_token_hash("token")
    metadata_path = tmp_path / token_hash / "metadata.json"
    data = json.loads(metadata_path.read_text())

    assert data[0]["domain"] == "*.example.com"
    assert data[0]["domains"] == ["*.Example.COM."]
    assert data[0]["cert_path"] == "_.example.com/cert.pem"
    assert data[0]["key_path"] == "_.example.com/privkey.pem"
