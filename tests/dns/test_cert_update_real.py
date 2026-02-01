#!/usr/bin/env python3
import pytest
import asyncio
import os
import sys
from pathlib import Path
from chattool.tools.dns.cert_updater import SSLCertUpdater
from chattool.utils import setup_logger

@pytest.mark.asyncio
async def test_cert_update():
    # Setup paths
    test_dir = Path("tests/testfiles/cert")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    cert_dir = test_dir / "certs"
    
    logger = setup_logger("test_cert_updater", log_level="INFO")
    
    domains = [
        "*.local.rexwang.site",
        "demo.public.rexwang.site"
    ]
    email = "admin@rexwang.site" # Dummy email for test
    
    updater = SSLCertUpdater(
        domains=domains,
        email=email,
        cert_dir=str(cert_dir),
        staging=True, # Use staging environment
        logger=logger,
        dns_type='tencent' # Assuming we use Tencent for these domains
    )
    
    # Run
    await updater.run_once()
    
    # Verification logic
    main_domain_dir = cert_dir / "_.local.rexwang.site"
    assert main_domain_dir.exists()
    assert (main_domain_dir / "fullchain.pem").exists()
    assert (main_domain_dir / "privkey.pem").exists()
    assert (main_domain_dir / "cert.pem").exists()
    # chain.pem might be empty if no intermediates (unlikely for LE staging)
    
    print("Verification Successful: All cert files generated correctly.")

if __name__ == "__main__":
    asyncio.run(test_cert_update())
