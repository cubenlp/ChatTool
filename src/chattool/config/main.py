from .elements import BaseEnvConfig, EnvField

# ==================== 具体服务配置定义 ====================

class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    
    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API (with suffix /v1). Overrides OPENAI_API_BASE_URL.")
    OPENAI_API_BASE_URL = EnvField("OPENAI_API_BASE_URL", desc="The base url of the API (without suffix /v1)")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-3.5-turbo", desc="The default model name")

class AzureConfig(BaseEnvConfig):
    _title = "Azure OpenAI Configuration"
    _aliases = ["azure", "az"]
    
    AZURE_OPENAI_API_KEY = EnvField("AZURE_OPENAI_API_KEY", desc="Azure OpenAI API Key", is_sensitive=True)
    AZURE_OPENAI_ENDPOINT = EnvField("AZURE_OPENAI_ENDPOINT", desc="Azure OpenAI Endpoint")
    AZURE_OPENAI_API_VERSION = EnvField("AZURE_OPENAI_API_VERSION", desc="Azure OpenAI API Version")
    AZURE_OPENAI_API_MODEL = EnvField("AZURE_OPENAI_API_MODEL", desc="Azure OpenAI Deployment Name (Model)")

class AliyunConfig(BaseEnvConfig):
    _title = "Alibaba Cloud (Aliyun) Configuration"
    _aliases = ["ali", "aliyun", "alidns"]
    
    ALIBABA_CLOUD_ACCESS_KEY_ID = EnvField("ALIBABA_CLOUD_ACCESS_KEY_ID", desc="Access Key ID. See https://www.alibabacloud.com/help/zh/ram/user-guide/create-an-accesskey-pair", is_sensitive=True)
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = EnvField("ALIBABA_CLOUD_ACCESS_KEY_SECRET", desc="Access Key Secret", is_sensitive=True)
    ALIBABA_CLOUD_REGION_ID = EnvField("ALIBABA_CLOUD_REGION_ID", default="cn-hangzhou", desc="Region ID (default: cn-hangzhou)")

class TencentConfig(BaseEnvConfig):
    _title = "Tencent Cloud Configuration"
    _aliases = ["tencent", "tx", "tencent-dns"]
    
    TENCENT_SECRET_ID = EnvField("TENCENT_SECRET_ID", desc="Secret ID. See https://console.cloud.tencent.com.cn/cam/capi", is_sensitive=True)
    TENCENT_SECRET_KEY = EnvField("TENCENT_SECRET_KEY", desc="Secret Key", is_sensitive=True)
    TENCENT_REGION_ID = EnvField("TENCENT_REGION_ID", default="ap-guangzhou", desc="Region ID (default: ap-guangzhou)")

class ZulipConfig(BaseEnvConfig):
    _title = "Zulip Configuration"
    _aliases = ["zulip"]
    
    ZULIP_BOT_EMAIL = EnvField("ZULIP_BOT_EMAIL", desc="Zulip Bot Email")
    ZULIP_BOT_API_KEY = EnvField("ZULIP_BOT_API_KEY", desc="Zulip Bot API Key", is_sensitive=True)
    ZULIP_SITE = EnvField("ZULIP_SITE", desc="Zulip Site URL")
