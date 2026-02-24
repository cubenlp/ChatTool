from .elements import BaseEnvConfig, EnvField

# ==================== 具体服务配置定义 ====================

class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    
    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API (with suffix /v1). Overrides OPENAI_API_BASE_URL.")
    OPENAI_API_BASE_URL = EnvField("OPENAI_API_BASE_URL", desc="The base url of the API (without suffix /v1)")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-3.5-turbo", desc="The default model name")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.llm.chattype import Chat
            # 使用 max_tokens=5 减少消耗，仅测试连通性
            chat = Chat(messages=[{"role": "user", "content": "hi"}])
            resp = chat.get_response(max_tokens=5)
            print(f"✅ Success! Response: {resp.content}")
        except Exception as e:
            print(f"❌ Failed: {e}")

class AzureConfig(BaseEnvConfig):
    _title = "Azure OpenAI Configuration"
    _aliases = ["azure", "az"]
    
    AZURE_OPENAI_API_KEY = EnvField("AZURE_OPENAI_API_KEY", desc="Azure OpenAI API Key", is_sensitive=True)
    AZURE_OPENAI_ENDPOINT = EnvField("AZURE_OPENAI_ENDPOINT", desc="Azure OpenAI Endpoint")
    AZURE_OPENAI_API_VERSION = EnvField("AZURE_OPENAI_API_VERSION", desc="Azure OpenAI API Version")
    AZURE_OPENAI_API_MODEL = EnvField("AZURE_OPENAI_API_MODEL", desc="Azure OpenAI Deployment Name (Model)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.llm.chattype import AzureChat
            chat = AzureChat(messages=[{"role": "user", "content": "hi"}])
            resp = chat.get_response(max_tokens=5)
            print(f"✅ Success! Response: {resp.content}")
        except Exception as e:
            print(f"❌ Failed: {e}")

class AliyunConfig(BaseEnvConfig):
    _title = "Alibaba Cloud (Aliyun) Configuration"
    _aliases = ["ali", "aliyun", "alidns"]
    
    ALIBABA_CLOUD_ACCESS_KEY_ID = EnvField("ALIBABA_CLOUD_ACCESS_KEY_ID", desc="Access Key ID. See https://www.alibabacloud.com/help/zh/ram/user-guide/create-an-accesskey-pair", is_sensitive=True)
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = EnvField("ALIBABA_CLOUD_ACCESS_KEY_SECRET", desc="Access Key Secret", is_sensitive=True)
    ALIBABA_CLOUD_REGION_ID = EnvField("ALIBABA_CLOUD_REGION_ID", default="cn-hangzhou", desc="Region ID (default: cn-hangzhou)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.dns.aliyun import AliyunDNSClient
            client = AliyunDNSClient()
            # 尝试获取域名列表，只取1个来验证
            domains = client.describe_domains(page_size=1)
            print(f"✅ Success! API call successful. Found {len(domains)} domains (in first page).")
        except Exception as e:
            print(f"❌ Failed: {e}")

class TencentConfig(BaseEnvConfig):
    _title = "Tencent Cloud Configuration"
    _aliases = ["tencent", "tx", "tencent-dns"]
    
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

class ZulipConfig(BaseEnvConfig):
    _title = "Zulip Configuration"
    _aliases = ["zulip"]
    
    ZULIP_BOT_EMAIL = EnvField("ZULIP_BOT_EMAIL", desc="Zulip Bot Email")
    ZULIP_BOT_API_KEY = EnvField("ZULIP_BOT_API_KEY", desc="Zulip Bot API Key", is_sensitive=True)
    ZULIP_SITE = EnvField("ZULIP_SITE", desc="Zulip Site URL")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.zulip.client import ZulipClient
            client = ZulipClient()
            profile = client.get_profile()
            print(f"✅ Success! Authenticated as: {profile.get('email')} ({profile.get('full_name')})")
        except Exception as e:
            print(f"❌ Failed: {e}")

class FeishuConfig(BaseEnvConfig):
    _title = "Feishu Configuration"
    _aliases = ["feishu"]
    
    FEISHU_APP_ID = EnvField("FEISHU_APP_ID", desc="Feishu App ID (Get from https://open.feishu.cn/app)")
    FEISHU_APP_SECRET = EnvField("FEISHU_APP_SECRET", desc="Feishu App Secret", is_sensitive=True)
    FEISHU_API_BASE = EnvField("FEISHU_API_BASE", default="https://open.feishu.cn", desc="Feishu API Base URL (Default: https://open.feishu.cn, for Lark: https://open.larksuite.com)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.lark.bot import LarkBot
            bot = LarkBot()
            # 简单验证初始化
            print(f"✅ Success! LarkBot initialized with App ID: {bot.config.FEISHU_APP_ID.mask_value()}")
            print(f"   API Base: {bot.config.FEISHU_API_BASE.value}")
        except Exception as e:
            print(f"❌ Failed: {e}")
