import pytest
import socket
import netifaces
from unittest.mock import patch
from chattool.tools.dns.ip_updater import DynamicIPUpdater

class TestDynamicIPUpdater:
    
    @pytest.mark.asyncio
    async def test_get_ip_public(self):
        """Test getting public IP (default)"""
        updater = DynamicIPUpdater(domain_name="example.com", rr="test", ip_type='public')
        
        with patch.object(updater, 'get_public_ip', return_value="1.2.3.4") as mock_public:
            ip = await updater.get_ip()
            assert ip == "1.2.3.4"
            mock_public.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_get_ip_local_simple(self):
        """Test getting local IP without filtering"""
        updater = DynamicIPUpdater(domain_name="example.com", rr="test", ip_type='local')
        
        # Mock netifaces to return a predictable interface
        with patch('netifaces.interfaces', return_value=['eth0']), \
             patch('netifaces.ifaddresses') as mock_ifaddr:
             
            mock_ifaddr.return_value = {
                netifaces.AF_INET: [{'addr': '192.168.1.100'}]
            }
            
            ip = await updater.get_ip()
            assert ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_ip_local_cidr_filter(self):
        """Test getting local IP with CIDR filtering"""
        updater = DynamicIPUpdater(
            domain_name="example.com", 
            rr="test", 
            ip_type='local',
            local_ip_cidr='10.0.0.0/8'
        )
        
        with patch('netifaces.interfaces', return_value=['eth0', 'eth1']), \
             patch('netifaces.ifaddresses') as mock_ifaddr:
             
            # Setup mock to return different IPs for different calls
            def side_effect(iface):
                if iface == 'eth0':
                    return {netifaces.AF_INET: [{'addr': '192.168.1.100'}]}
                elif iface == 'eth1':
                    return {netifaces.AF_INET: [{'addr': '10.10.10.10'}]}
                return {}
            
            mock_ifaddr.side_effect = side_effect
            
            ip = await updater.get_ip()
            assert ip == "10.10.10.10"

    @pytest.mark.asyncio
    async def test_get_ip_local_no_match(self):
        """Test when no matching local IP is found"""
        updater = DynamicIPUpdater(
            domain_name="example.com", 
            rr="test", 
            ip_type='local',
            local_ip_cidr='172.16.0.0/12'
        )
        
        with patch('netifaces.interfaces', return_value=['eth0']), \
             patch('netifaces.ifaddresses') as mock_ifaddr:
             
            mock_ifaddr.return_value = {
                netifaces.AF_INET: [{'addr': '192.168.1.100'}]
            }
            
            ip = await updater.get_ip()
            assert ip is None
