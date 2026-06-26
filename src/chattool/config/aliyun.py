"""AliyunConfig env schema."""

from .base import BaseEnvConfig, EnvField


class AliyunConfig(BaseEnvConfig):
    _title = "Alibaba Cloud (Aliyun) Configuration"
    _aliases = ["ali", "aliyun", "alidns"]
    _storage_dir = "Aliyun"

    ALIBABA_CLOUD_ACCESS_KEY_ID = EnvField("ALIBABA_CLOUD_ACCESS_KEY_ID", desc="Access Key ID. See https://www.alibabacloud.com/help/zh/ram/user-guide/create-an-accesskey-pair", is_sensitive=True)
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = EnvField("ALIBABA_CLOUD_ACCESS_KEY_SECRET", desc="Access Key Secret", is_sensitive=True)
    ALIBABA_CLOUD_REGION_ID = EnvField("ALIBABA_CLOUD_REGION_ID", default="cn-hangzhou", desc="Region ID (default: cn-hangzhou)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chatdns import AliyunDNSClient
            client = AliyunDNSClient()
            # 尝试获取域名列表，只取1个来验证
            domains = client.describe_domains(page_size=1)
            print(f"✅ Success! API call successful. Found {len(domains)} domains (in first page).")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["AliyunConfig"]
