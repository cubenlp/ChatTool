#!/usr/bin/env python3
import pytest
import asyncio
import os
import shutil
import time
from pathlib import Path
from fastapi.testclient import TestClient
from chattool.tools.cert.cert_server import app, config

# Use TestClient for API testing
client = TestClient(app)

@pytest.mark.dns
# @pytest.mark.asyncio # TestClient is synchronous, no need for asyncio mark unless we use async features in test
class TestCertServerReal:
    """
    Integration tests for SSL Certificate Server with real ACME and Aliyun DNS.
    """
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Configuration
        self.test_token = "test-token-real"
        self.test_dir = Path("tests/testfiles/cert_server_real")
        self.test_domains = ["qpetlover.cn", "*.qpetlover.cn"]
        self.test_email = "admin@qpetlover.cn"
        
        # Setup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Update server config
        config["cert_dir"] = str(self.test_dir)
        config["token"] = self.test_token # Not used by TestClient dependency override, but good for consistency
        config["provider"] = "aliyun"
        
        # Note: Aliyun credentials should be in environment variables:
        # ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET
        
        yield
        
        # Teardown (Optional: keep files for inspection if failed)
        # if self.test_dir.exists():
        #     shutil.rmtree(self.test_dir)

    def test_cert_lifecycle(self):
        """
        Test the full lifecycle: Apply -> Poll Status -> List -> Download
        Using synchronous TestClient (which handles async endpoints).
        """
        headers = {"X-ChatTool-Token": self.test_token}
        
        # 1. Apply for certificate
        print(f"\n[1] Applying for certificate: {self.test_domains}")
        payload = {
            "domains": self.test_domains,
            "email": self.test_email,
            "provider": "aliyun",
        }

        response = client.post("/cert/apply", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        
        print("[2] Background task should be completed. Checking list...")
        
        # 2. List certificates to verify success
        response = client.get("/cert/list", headers=headers)
        assert response.status_code == 200
        cert_list = response.json()
        
        # Debug output
        print(f"Cert List: {cert_list}")
        
        assert len(cert_list) > 0
        record = cert_list[0]
        assert record["domain"] == "qpetlover.cn"
        assert record["domains"] == self.test_domains
        assert record["cert_path"]
        assert record["key_path"]
        
        # 3. Download files
        print("[3] Downloading certificate files...")
        
        # Main domain dir name (wildcard replaced)
        domain_dir = "qpetlover.cn" # In this case, main domain is qpetlover.cn, no wildcard prefix
        # Wait, if domains are ["qpetlover.cn", "*.qpetlover.cn"], main is "qpetlover.cn"
        # file_domain_name = "qpetlover.cn".replace("*", "_") -> "qpetlover.cn"
        
        # Download cert
        cert_path = record["cert_path"] # e.g. "qpetlover.cn/cert.pem"
        # API expects {domain}/{filename}
        # record["cert_path"] is relative to user_dir.
        # Let's split it.
        domain_part, filename = cert_path.split("/")
        
        resp = client.get(f"/cert/download/{domain_part}/{filename}", headers=headers)
        assert resp.status_code == 200
        assert b"BEGIN CERTIFICATE" in resp.content
        print(f"Downloaded {filename} successfully.")
        
        # Download key
        key_path = record["key_path"]
        domain_part, filename = key_path.split("/")
        resp = client.get(f"/cert/download/{domain_part}/{filename}", headers=headers)
        assert resp.status_code == 200
        assert b"PRIVATE KEY" in resp.content
        print(f"Downloaded {filename} successfully.")

        print("\n[Success] Full certificate lifecycle test passed.")

if __name__ == "__main__":
    # Manually run the test if executed as script
    t = TestCertServerReal()
    # Need to manually setup generator
    gen = t.setup_teardown()
    next(gen)
    try:
        t.test_cert_lifecycle()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
