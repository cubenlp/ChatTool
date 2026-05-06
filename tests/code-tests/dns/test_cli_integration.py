import pytest
from click.testing import CliRunner
from chattool.client.main import cli
from chattool.config import AliyunConfig, TencentConfig

@pytest.fixture
def runner():
    return CliRunner()

@pytest.mark.dns
@pytest.mark.integration
class TestDNSIntegration:
    """DNS CLI Integration Tests - Real Production Tests"""

    def test_dns_list_help(self, runner):
        """Test dns get help command"""
        result = runner.invoke(cli, ['dns', 'get', '--help'])
        assert result.exit_code == 0
        assert 'Show DNS record details.' in result.output

        result = runner.invoke(cli, ['dns', 'list', '--help'])
        assert result.exit_code == 0
        assert 'List DNS domains' in result.output

        result = runner.invoke(cli, ['dns', 'delete', '--help'])
        assert result.exit_code == 0
        assert 'Delete DNS records' in result.output

    def test_dns_ddns_help(self, runner):
        """Test dns ddns help command"""
        result = runner.invoke(cli, ['dns', 'ddns', '--help'])
        assert result.exit_code == 0
        assert 'Run dynamic DNS updates' in result.output

    def test_dns_cert_help(self, runner):
        """Test dns cert help command"""
        result = runner.invoke(cli, ['dns', 'cert', '--help'])
        assert result.exit_code == 0
        assert 'apply' in result.output
        assert 'check' in result.output

    def test_dns_list_tencent_real(self, runner):
        """Real integration test for Tencent DNS (rexwang.site)"""
        if not (TencentConfig.TENCENT_SECRET_ID.value and TencentConfig.TENCENT_SECRET_KEY.value):
            pytest.skip("Tencent DNS credentials are not configured")
        # Ensure we are using the correct provider
        result = runner.invoke(cli, ['dns', 'get', '-d', 'rexwang.site', '-p', 'tencent'])
        print(f"Tencent Result: {result.output}")
        if result.exit_code != 0:
            pytest.fail(f"Tencent DNS list failed: {result.output}")
        assert result.exit_code == 0
        # Output format changed: "DNS记录 (tencent):"
        assert 'DNS记录' in result.output

    def test_dns_list_aliyun_real(self, runner):
        """Real integration test for Aliyun DNS (qpetlover.cn)"""
        if not (
            AliyunConfig.ALIBABA_CLOUD_ACCESS_KEY_ID.value
            and AliyunConfig.ALIBABA_CLOUD_ACCESS_KEY_SECRET.value
        ):
            pytest.skip("Aliyun DNS credentials are not configured")
        # Ensure we are using the correct provider
        result = runner.invoke(cli, ['dns', 'get', '-d', 'qpetlover.cn', '-p', 'aliyun'])
        print(f"Aliyun Result: {result.output}")
        if result.exit_code != 0:
            pytest.fail(f"Aliyun DNS list failed: {result.output}")
        assert result.exit_code == 0
        assert 'DNS记录' in result.output
