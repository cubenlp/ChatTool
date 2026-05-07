"""TencentConfig env schema."""

from .base import BaseEnvConfig, EnvField


class TencentConfig(BaseEnvConfig):
    _title = "Tencent Cloud Configuration"
    _aliases = ["tencent", "tx", "tencent-dns"]
    _storage_dir = "Tencent"

    TENCENT_SECRET_ID = EnvField("TENCENT_SECRET_ID", desc="Secret ID. See https://console.cloud.tencent.com.cn/cam/capi", is_sensitive=True)
    TENCENT_SECRET_KEY = EnvField("TENCENT_SECRET_KEY", desc="Secret Key", is_sensitive=True)
    TENCENT_REGION_ID = EnvField("TENCENT_REGION_ID", default="ap-guangzhou", desc="Region ID (default: ap-guangzhou)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.dns.tencent import TencentDNSClient
            client = TencentDNSClient()
            domains = client.describe_domains(page_size=1)
            print(f"✅ Success! API call successful. Found {len(domains)} domains (in first page).")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["TencentConfig"]
