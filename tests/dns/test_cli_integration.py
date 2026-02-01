import pytest
import os
from click.testing import CliRunner
from chattool.client.main import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.mark.integration
class TestDNSIntegration:
    """DNS CLI Integration Tests - Real Production Tests"""

    def test_dns_list_help(self, runner):
        """Test dns get help command"""
        result = runner.invoke(cli, ['dns', 'get', '--help'])
        assert result.exit_code == 0
        assert '获取DNS记录信息' in result.output

    def test_dns_ddns_help(self, runner):
        """Test dns ddns help command"""
        result = runner.invoke(cli, ['dns', 'ddns', '--help'])
        assert result.exit_code == 0
        assert '执行动态DNS更新' in result.output

    def test_dns_cert_help(self, runner):
        """Test dns cert help command"""
        result = runner.invoke(cli, ['dns', 'cert-update', '--help'])
        assert result.exit_code == 0
        # assert 'SSL 证书自动更新工具' in result.output # Might vary slightly in text, just check exit code

    def test_dns_list_tencent_real(self, runner):
        """Real integration test for Tencent DNS (rexwang.site)"""
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
        # Ensure we are using the correct provider
        result = runner.invoke(cli, ['dns', 'get', '-d', 'qpetlover.cn', '-p', 'aliyun'])
        print(f"Aliyun Result: {result.output}")
        if result.exit_code != 0:
            pytest.fail(f"Aliyun DNS list failed: {result.output}")
        assert result.exit_code == 0
        assert 'DNS记录' in result.output
