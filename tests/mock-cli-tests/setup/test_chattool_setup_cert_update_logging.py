import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_dns_cert_update_accepts_log_level_option(monkeypatch, runner):
    captured = {}

    class DummyLogger:
        def info(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            pass

    class DummyUpdater:
        def __init__(self, **kwargs):
            captured["logger"] = kwargs["logger"]

        async def run_once(self):
            return True

    def fake_setup_logger(name, log_file=None, log_level="INFO", **kwargs):
        captured["name"] = name
        captured["log_file"] = log_file
        captured["log_level"] = log_level
        return DummyLogger()

    monkeypatch.setattr("chattool.tools.cert.cli.setup_logger", fake_setup_logger)
    monkeypatch.setattr("chattool.tools.cert.cli.SSLCertUpdater", DummyUpdater)

    result = runner.invoke(
        cli,
        [
            "dns",
            "cert-update",
            "--domains",
            "example.com",
            "--email",
            "admin@example.com",
            "--log-level",
            "DEBUG",
            "-I",
        ],
    )

    assert result.exit_code == 0
    assert captured["name"] == "ssl_cert_updater"
    assert captured["log_level"] == "DEBUG"
