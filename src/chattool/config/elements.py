import os
from typing import Dict, Any, List, Type
import dotenv
import chattool

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
            
        return chattool.mask_secret(api_key)

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
    def set(cls, key: str, value: Any):
        """设置配置值"""
        for config_cls in cls._registry:
            fields = config_cls.get_fields()
            if key in fields:
                fields[key].value = value
                return
        # Optional: raise error or warn if key not found
        # print(f"Warning: Configuration key '{key}' not found.")
    
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
    def save_env_file(cls, env_path: str, version: str = "0.0.0"):
        """保存当前配置到 .env 文件"""
        content = cls.generate_env_template(version)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)

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
