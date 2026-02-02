import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock, ANY

@pytest.mark.dns
@pytest.mark.asyncio
class TestMCPServer:
    
    async def test_dns_list_domains(self):
        """Test dns_list_domains tool"""
        with patch('chattool.mcp.dns.create_dns_client') as mock_create:
            mock_client = MagicMock()
            mock_client.describe_domains.return_value = [{'DomainName': 'example.com'}]
            mock_create.return_value = mock_client
            
            from chattool.mcp.dns import list_domains
            
            result = list_domains(provider='aliyun')
            assert len(result) == 1
            assert result[0]['DomainName'] == 'example.com'
            mock_create.assert_called_with('aliyun', logger=ANY)

    async def test_dns_add_record(self):
        """Test dns_add_record tool"""
        with patch('chattool.mcp.dns.create_dns_client') as mock_create:
            mock_client = MagicMock()
            mock_client.add_domain_record.return_value = '12345'
            mock_create.return_value = mock_client
            
            from chattool.mcp.dns import add_record
            
            result = add_record(
                domain='example.com', 
                rr='www', 
                type='A', 
                value='1.1.1.1',
                provider='tencent'
            )
            
            assert result == '12345'
            mock_create.assert_called_with('tencent', logger=ANY)
            mock_client.add_domain_record.assert_called_with(
                'example.com', 'www', 'A', '1.1.1.1', 600
            )

    async def test_dns_ddns_update(self):
        """Test dns_ddns_update tool"""
        with patch('chattool.mcp.dns.DynamicIPUpdater') as MockUpdater:
            instance = MockUpdater.return_value
            instance.run_once = AsyncMock(return_value=True)
            
            from chattool.mcp.dns import ddns_update
            
            result = await ddns_update(
                domain='example.com', 
                rr='home',
                provider='aliyun'
            )
            
            assert result is True
            MockUpdater.assert_called_with(
                domain_name='example.com',
                rr='home',
                dns_type='aliyun',
                ip_type='public',
                logger=ANY
            )

    async def test_dns_cert_update(self):
        """Test dns_cert_update tool"""
        with patch('chattool.mcp.dns.SSLCertUpdater') as MockUpdater:
            instance = MockUpdater.return_value
            instance.run_once = AsyncMock(return_value=True)
            
            from chattool.mcp.dns import cert_update
            
            domains = ['example.com', '*.example.com']
            email = 'admin@example.com'
            
            result = await cert_update(
                domains=domains,
                email=email,
                provider='aliyun',
                staging=True
            )
            
            assert result is True
            MockUpdater.assert_called_with(
                domains=domains,
                email=email,
                dns_type='aliyun',
                staging=True,
                logger=ANY
            )
