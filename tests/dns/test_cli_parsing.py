import pytest
from unittest.mock import patch, AsyncMock
from chattool.cli.client.dns_updater import ddns
from click.testing import CliRunner
from chattool.cli.main import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.mark.dns
@pytest.mark.integration
class TestDNSCLIUsage:
    """Tests for new CLI usage patterns (positional arguments)"""

    def test_ddns_full_domain(self, runner):
        """Test ddns with positional argument: chattool dns ddns test.rexwang.site"""
        # We assume 'test.rexwang.site' parses to domain=rexwang.site, rr=test
        # We'll use --help to check if it parses arguments correctly without running actual update
        # Or mock the updater to verify arguments passed.
        
        # Since this is integration test, we can try running it with dry-run-ish behavior?
        # Or just rely on mocking inside a unit test. 
        # Let's create a unit test file for CLI parsing logic if we want to be safe without network.
        pass

    def test_ddns_argument_parsing(self, runner):
        """Verify that full_domain is correctly split into domain and rr"""
        
        # We can use invoke and check for error if domain is invalid, or success if valid
        # But we don't want to actually update DNS in this test.
        # So we'll mock DynamicIPUpdater
        
        with patch('chattool.cli.client.dns_updater.DynamicIPUpdater') as MockUpdater:
            # Mock run_once as an async method returning True
            instance = MockUpdater.return_value
            instance.run_once = AsyncMock(return_value=True)
            
            # Case 1: Standard 3-part domain
            result = runner.invoke(cli, ['dns', 'ddns', 'test.rexwang.site'])
            assert result.exit_code == 0
            call_args = MockUpdater.call_args[1]
            assert call_args['domain_name'] == 'rexwang.site'
            assert call_args['rr'] == 'test'
            
            # Case 2: 2-part domain (rr=@)
            result = runner.invoke(cli, ['dns', 'ddns', 'rexwang.site'])
            assert result.exit_code == 0
            call_args = MockUpdater.call_args[1]
            assert call_args['domain_name'] == 'rexwang.site'
            assert call_args['rr'] == '@'
            
            # Case 3: 4-part domain
            result = runner.invoke(cli, ['dns', 'ddns', 'a.b.rexwang.site'])
            assert result.exit_code == 0
            call_args = MockUpdater.call_args[1]
            assert call_args['domain_name'] == 'rexwang.site'
            assert call_args['rr'] == 'a.b'

            # Case 4: Mix (warning should appear)
            result = runner.invoke(cli, ['dns', 'ddns', 'test.rexwang.site', '-d', 'other.com'])
            assert result.exit_code == 0
            assert "警告" in result.output
            call_args = MockUpdater.call_args[1]
            assert call_args['domain_name'] == 'rexwang.site' # Positional wins

            # Case 5: Use Options (no positional)
            result = runner.invoke(cli, ['dns', 'ddns', '-d', 'example.com', '-r', 'www'])
            assert result.exit_code == 0
            call_args = MockUpdater.call_args[1]
            assert call_args['domain_name'] == 'example.com'
            assert call_args['rr'] == 'www'

            # Case 6: Missing all args
            result = runner.invoke(cli, ['dns', 'ddns'])
            assert result.exit_code != 0
            assert "必须提供 full_domain 位置参数，或者同时提供 --domain 和 --rr 选项" in result.output
