import pytest
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


@pytest.fixture
def runner():
    return CliRunner()


def test_dns_help_commands(runner):
    result = runner.invoke(cli, ["dns", "list", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "records", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "delete", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "ip", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "ddns", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "cert", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "cert", "apply", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["dns", "cert", "check", "--help"])
    assert result.exit_code == 0


def test_dns_ddns_argument_parsing(runner):
    with patch("chattool.tools.dns.cli.DynamicIPUpdater") as MockUpdater:
        instance = MockUpdater.return_value
        instance.run_once = AsyncMock(return_value=True)

        result = runner.invoke(cli, ["dns", "ddns", "test.rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "test"

        result = runner.invoke(cli, ["dns", "ddns", "rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "@"

        result = runner.invoke(cli, ["dns", "ddns", "a.b.rexwang.site"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"
        assert call_args["rr"] == "a.b"

        result = runner.invoke(
            cli, ["dns", "ddns", "test.rexwang.site", "-d", "other.com"]
        )
        assert result.exit_code == 0
        assert "警告" in result.output
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "rexwang.site"

        result = runner.invoke(cli, ["dns", "ddns", "-d", "example.com", "-r", "www"])
        assert result.exit_code == 0
        call_args = MockUpdater.call_args[1]
        assert call_args["domain_name"] == "example.com"
        assert call_args["rr"] == "www"

        result = runner.invoke(cli, ["dns", "ddns", "-I"])
        assert result.exit_code != 0
        assert "必须提供" in result.output


def test_dns_root_prompts_for_command_and_runs_set_flow(runner, monkeypatch):
    prompts = iter(["example.com", "www", "1.2.3.4"])

    monkeypatch.setattr("chattool.tools.dns.cli.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.tools.dns.cli.ask_select",
        lambda message, choices, style=None: "set - 创建或更新 DNS 记录",
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: next(prompts),
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.set_record_value.return_value = True

        result = runner.invoke(cli, ["dns"], catch_exceptions=False)

    assert result.exit_code == 0
    client.set_record_value.assert_called_once_with(
        "example.com", "www", "A", "1.2.3.4", 600
    )


def test_dns_set_prompts_when_required_args_missing(runner, monkeypatch):
    answers = {
        "domain": "example.com",
        "rr": "test",
        "value": "1.2.3.4",
    }

    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: answers[label],
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.set_record_value.return_value = True

        result = runner.invoke(cli, ["dns", "set"], catch_exceptions=False)

    assert result.exit_code == 0
    client.set_record_value.assert_called_once_with(
        "example.com", "test", "A", "1.2.3.4", 600
    )


def test_dns_set_errors_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["dns", "set", "-I"])

    assert result.exit_code != 0
    assert "必须提供 full_domain" in result.output


def test_dns_records_prompts_when_domain_missing(runner, monkeypatch):
    answers = {
        "domain": "example.com",
    }

    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda label, default="", password=False, style=None: answers[label],
    )

    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []

        result = runner.invoke(cli, ["dns", "records"], catch_exceptions=False)

    assert result.exit_code == 0
    client.describe_domain_records.assert_called_once_with(
        "example.com", subdomain=None, record_type=None
    )


def test_dns_records_set_parsing(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []
        client.set_record_value.return_value = True

        result = runner.invoke(cli, ["dns", "set", "test.example.com", "-v", "1.2.3.4"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["dns", "records", "test.example.com"])
        assert result.exit_code == 0
        client.describe_domain_records.assert_called_once_with(
            "example.com", subdomain="test", record_type=None
        )


def test_dns_records_root_domain_lists_all_records(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = []

        result = runner.invoke(cli, ["dns", "records", "example.com", "-t", "a"])

    assert result.exit_code == 0
    client.describe_domain_records.assert_called_once_with(
        "example.com", subdomain=None, record_type="A"
    )


def test_dns_list_domains(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domains.return_value = [
            {
                "DomainName": "example.com",
                "DomainId": "d-1",
                "Status": "ENABLE",
                "RecordCount": 3,
                "Remark": "demo",
            }
        ]

        result = runner.invoke(
            cli,
            ["dns", "list", "--provider", "tencent", "--page", "2", "--page-size", "5"],
        )

    assert result.exit_code == 0
    MockFactory.assert_called_once()
    client.describe_domains.assert_called_once_with(page_number=2, page_size=5)
    assert "DNS域名 (tencent)" in result.output
    assert "example.com" in result.output


def test_dns_delete_record_filters_and_deletes(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = [
            {
                "RecordId": "1",
                "RR": "test",
                "Type": "A",
                "Value": "1.2.3.4",
                "TTL": 600,
            },
            {
                "RecordId": "2",
                "RR": "test",
                "Type": "A",
                "Value": "5.6.7.8",
                "TTL": 600,
            },
        ]
        client.delete_domain_record.return_value = True

        result = runner.invoke(
            cli,
            [
                "dns",
                "delete",
                "test.example.com",
                "-t",
                "A",
                "-v",
                "1.2.3.4",
                "--yes",
                "-I",
            ],
        )

    assert result.exit_code == 0
    client.describe_domain_records.assert_called_once_with(
        "example.com", subdomain="test", record_type="A"
    )
    client.delete_domain_record.assert_called_once_with("1", domain_name="example.com")
    assert "删除成功: 1 条记录" in result.output


def test_dns_delete_requires_yes_when_interaction_disabled(runner):
    with patch("chattool.tools.dns.cli.create_dns_client") as MockFactory:
        client = MockFactory.return_value
        client.describe_domain_records.return_value = [
            {
                "RecordId": "1",
                "RR": "test",
                "Type": "A",
                "Value": "1.2.3.4",
                "TTL": 600,
            },
        ]

        result = runner.invoke(cli, ["dns", "delete", "test.example.com", "-t", "A", "-I"])

    assert result.exit_code != 0
    assert "非交互环境请传入 --yes" in result.output
    client.delete_domain_record.assert_not_called()


def test_dns_delete_requires_record_type_when_interaction_disabled(runner):
    result = runner.invoke(cli, ["dns", "delete", "test.example.com", "-I"])

    assert result.exit_code != 0
    assert "必须提供要删除的记录类型" in result.output


def test_dns_get_command_is_removed(runner):
    result = runner.invoke(cli, ["dns", "get", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_dns_ip_public(runner, monkeypatch):
    async def fake_public_ip():
        return "203.0.113.10"

    monkeypatch.setattr("chattool.tools.dns.cli._get_public_ip", fake_public_ip)

    result = runner.invoke(cli, ["dns", "ip"])

    assert result.exit_code == 0
    assert "203.0.113.10" in result.output


def test_dns_ip_local(runner, monkeypatch):
    monkeypatch.setattr(
        "chattool.tools.dns.cli._get_local_ip", lambda local_ip_cidr=None: "192.168.1.8"
    )

    result = runner.invoke(
        cli, ["dns", "ip", "--type", "local", "--local-ip-cidr", "192.168.1.0/24"]
    )

    assert result.exit_code == 0
    assert "192.168.1.8" in result.output


def test_dns_cert_apply_passes_new_interface_options(runner, monkeypatch):
    captured = {}

    class DummyLogger:
        def info(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            pass

    class DummyUpdater:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def run_once(self):
            return True

    monkeypatch.setattr("chattool.tools.cert.cli.SSLCertUpdater", DummyUpdater)
    monkeypatch.setattr(
        "chattool.tools.cert.cli.setup_logger", lambda *_args, **_kwargs: DummyLogger()
    )

    result = runner.invoke(
        cli,
        [
            "dns",
            "cert",
            "apply",
            "-d",
            "example.com",
            "-e",
            "admin@example.com",
            "--provider",
            "tencent",
            "--force",
            "-I",
        ],
    )

    assert result.exit_code == 0
    assert captured["domains"] == ["example.com"]
    assert captured["email"] == "admin@example.com"
    assert captured["dns_type"] == "tencent"
    assert captured["force"] is True


def test_dns_cert_apply_uses_git_email_default(runner, monkeypatch):
    captured = {}

    class DummyLogger:
        def info(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            pass

    class DummyUpdater:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def run_once(self):
            return True

    monkeypatch.setattr("chattool.tools.cert.cli.SSLCertUpdater", DummyUpdater)
    monkeypatch.setattr(
        "chattool.tools.cert.cli.setup_logger", lambda *_args, **_kwargs: DummyLogger()
    )
    monkeypatch.setattr(
        "chattool.tools.cert.cli.get_git_user_email", lambda: "git@example.com"
    )

    result = runner.invoke(cli, ["dns", "cert", "apply", "-d", "example.com", "-I"])

    assert result.exit_code == 0
    assert captured["email"] == "git@example.com"


def test_dns_cert_update_is_removed(runner):
    result = runner.invoke(cli, ["dns", "cert-update", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output
