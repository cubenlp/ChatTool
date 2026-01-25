import os
from typing import Dict, Any, List, Optional, Type
import dotenv

class EnvField:
    """环境变量字段描述符"""
    def __init__(self, env_key: str, default: Any = None, desc: str = "", is_sensitive: bool = False):
        self.env_key = env_key
        self.default = default
        self.desc = desc
        self.is_sensitive = is_sensitive
        self.value = default # 运行时值

    def __repr__(self):
        return f"EnvField(key={self.env_key}, default={self.default})"
    
    def mask_value(self) -> str:
        """获取掩码后的值"""
        api_key = self.value
        if not api_key:
            return ""
        if not self.is_sensitive:
            return str(api_key)
            
        length = len(api_key)
        if length == 1 or length == 2:
            masked_key = '*' * length
        elif 3 <= length <= 6:
            masked_key = api_key[0] + '*' * (length - 2) + api_key[-1]
        elif 7 <= length <= 14:
            masked_key = api_key[:2] + '*' * (length - 4) + api_key[-2:]
        elif 15 <= length <= 30:
            masked_key = api_key[:4] + '*' * (length - 8) + api_key[-4:]
        else:
            masked_key = api_key[:8] + '*' * (length - 12) + api_key[-8:]
        return masked_key

class BaseEnvConfig:
    """环境变量配置基类"""
    
    _registry: List[Type['BaseEnvConfig']] = []
    _title: str = "Configuration"

    def __init_subclass__(cls, **kwargs):
        """自动注册子类"""
        super().__init_subclass__(**kwargs)
        cls._registry.append(cls)

    @classmethod
    def get_fields(cls) -> Dict[str, EnvField]:
        """获取类中定义的所有 EnvField"""
        fields = {}
        for name, value in cls.__dict__.items():
            if isinstance(value, EnvField):
                fields[name] = value
        return fields

    @classmethod
    def load_from_dict(cls, env_values: Dict[str, str]):
        """从字典加载配置值"""
        for field in cls.get_fields().values():
            # 优先级: 传入的字典 > 系统环境变量 > 默认值
            val = env_values.get(field.env_key)
            if val is None:
                val = os.getenv(field.env_key)
            
            if val is not None:
                field.value = val
            else:
                field.value = field.default

    @classmethod
    def load_all(cls, env_path: str):
        """加载所有已注册服务的配置"""
        env_values = dotenv.dotenv_values(env_path)
        for config_cls in cls._registry:
            config_cls.load_from_dict(env_values)

    @classmethod
    def get_all_values(cls) -> Dict[str, Any]:
        """获取所有已加载的配置值（用于注入到 const）"""
        values = {}
        for config_cls in cls._registry:
            for name, field in config_cls.get_fields().items():
                values[name] = field.value
        return values
    
    @classmethod
    def generate_env_template(cls, current_version: str) -> str:
        """生成 .env 文件模板"""
        lines = [
            f"# Description: Env file for ChatTool.",
            f"# Current version: {current_version}",
            ""
        ]
        
        for config_cls in cls._registry:
            lines.append(f"# ==================== {config_cls._title} ====================")
            for _, field in config_cls.get_fields().items():
                if field.desc:
                    lines.append(f"# {field.desc}")
                
                # 处理值的显示
                val_str = str(field.value) if field.value is not None else ''
                # 如果是字符串且包含空格等，可能需要引号，这里简单处理
                lines.append(f"{field.env_key}='{val_str}'")
                lines.append("") # 空行分隔
            
        return "\n".join(lines)

    @classmethod
    def print_config(cls):
        """打印配置信息（敏感信息自动打码）"""
        for config_cls in cls._registry:
            print(f"\n{config_cls._title}:")
            for name, field in config_cls.get_fields().items():
                if field.value:
                    if field.is_sensitive:
                        print(f"  {name}: {field.mask_value()}")
                    else:
                        print(f"  {name}: {field.value}")
                else:
                    # 可选：如果没值，可以不打印或者打印提示
                    # print(f"  {name}: <not set>")
                    pass

# ==================== 具体服务配置定义 ====================

class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    
    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API (with suffix /v1). Overrides OPENAI_API_BASE_URL.")
    OPENAI_API_BASE_URL = EnvField("OPENAI_API_BASE_URL", desc="The base url of the API (without suffix /v1)")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-3.5-turbo", desc="The default model name")

class AzureConfig(BaseEnvConfig):
    _title = "Azure OpenAI Configuration"
    
    AZURE_OPENAI_API_KEY = EnvField("AZURE_OPENAI_API_KEY", desc="Azure OpenAI API Key", is_sensitive=True)
    AZURE_OPENAI_ENDPOINT = EnvField("AZURE_OPENAI_ENDPOINT", desc="Azure OpenAI Endpoint")
    AZURE_OPENAI_API_VERSION = EnvField("AZURE_OPENAI_API_VERSION", desc="Azure OpenAI API Version")
    AZURE_OPENAI_API_MODEL = EnvField("AZURE_OPENAI_API_MODEL", desc="Azure OpenAI Deployment Name (Model)")

class AliyunConfig(BaseEnvConfig):
    _title = "Alibaba Cloud (Aliyun) Configuration"
    
    ALIBABA_CLOUD_ACCESS_KEY_ID = EnvField("ALIBABA_CLOUD_ACCESS_KEY_ID", desc="Access Key ID", is_sensitive=True)
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = EnvField("ALIBABA_CLOUD_ACCESS_KEY_SECRET", desc="Access Key Secret", is_sensitive=True)
    ALIBABA_CLOUD_REGION_ID = EnvField("ALIBABA_CLOUD_REGION_ID", default="cn-hangzhou", desc="Region ID (default: cn-hangzhou)")

class TencentConfig(BaseEnvConfig):
    _title = "Tencent Cloud Configuration"
    
    TENCENT_SECRET_ID = EnvField("TENCENT_SECRET_ID", desc="Secret ID", is_sensitive=True)
    TENCENT_SECRET_KEY = EnvField("TENCENT_SECRET_KEY", desc="Secret Key", is_sensitive=True)
    TENCENT_REGION_ID = EnvField("TENCENT_REGION_ID", default="ap-guangzhou", desc="Region ID (default: ap-guangzhou)")

class ZulipConfig(BaseEnvConfig):
    _title = "Zulip Configuration"
    
    ZULIP_BOT_EMAIL = EnvField("ZULIP_BOT_EMAIL", desc="Zulip Bot Email")
    ZULIP_BOT_API_KEY = EnvField("ZULIP_BOT_API_KEY", desc="Zulip Bot API Key", is_sensitive=True)
    ZULIP_SITE = EnvField("ZULIP_SITE", desc="Zulip Site URL")
