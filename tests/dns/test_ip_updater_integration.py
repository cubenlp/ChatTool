import pytest
import os
import asyncio
from chattool.tools.dns.dynamic_ip_updater import DynamicIPUpdater
from chattool.utils import setup_logger

@pytest.mark.integration
class TestDynamicIPUpdaterIntegration:
    """Real integration tests for DynamicIPUpdater using Tencent DNS"""
    
    @pytest.fixture
    def logger(self):
        return setup_logger("test_dns_integration")

    @pytest.mark.asyncio
    async def test_update_public_ip(self, logger):
        """Test updating public IP for public.rexwang.site"""
        updater = DynamicIPUpdater(
            domain_name="rexwang.site",
            rr="public",
            dns_type="tencent",
            ip_type="public",
            logger=logger
        )
        
        logger.info("Starting Public IP update test for public.rexwang.site")
        success = await updater.run_once()
        assert success is True, "Public IP update failed"

    @pytest.mark.asyncio
    async def test_update_local_ip(self, logger):
        """Test updating local IP for local.rexwang.site (192.168.0.0/16)"""
        updater = DynamicIPUpdater(
            domain_name="rexwang.site",
            rr="local",
            dns_type="tencent",
            ip_type="local",
            local_ip_cidr="192.168.0.0/16",
            logger=logger
        )
        
        logger.info("Starting Local IP update test for local.rexwang.site")
        
        # Check if we can actually get a local IP first
        local_ip = updater.get_local_ip()
        if not local_ip:
            pytest.skip("No local IP found in 192.168.0.0/16 range, skipping test")
            
        success = await updater.run_once()
        assert success is True, "Local IP update failed"
