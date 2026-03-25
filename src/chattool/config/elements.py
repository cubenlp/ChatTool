import os
from pathlib import Path
from typing import Dict, Any, List, Type
import chattool
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
            
        return chattool.mask_secret(api_key)

class BaseEnvConfig:
    """环境变量配置基类"""
    
    _registry: List[Type['BaseEnvConfig']] = []
    _title: str = "Configuration"
    _storage_dir: str | None = None

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
    def get_storage_name(cls) -> str:
        return cls._storage_dir or cls.__name__.removesuffix("Config") or cls.__name__

    @classmethod
    def get_storage_dir(cls, env_root: str | Path) -> Path:
        return Path(env_root) / cls.get_storage_name()

    @classmethod
    def get_active_env_file(cls, env_root: str | Path) -> Path:
        return cls.get_storage_dir(env_root) / ".env"

    @classmethod
    def get_profile_env_file(cls, env_root: str | Path, name: str) -> Path:
        profile_name = str(name).strip()
        if not profile_name:
            raise ValueError("Profile name cannot be empty.")
        if not profile_name.endswith(".env"):
            profile_name += ".env"
        return cls.get_storage_dir(env_root) / profile_name

    @classmethod
    def render_env_file(cls) -> str:
        lines = [
            f"# Description: Env file for {cls._title}.",
            ""
        ]
        for _, field in cls.get_fields().items():
            if field.desc:
                lines.append(f"# {field.desc}")
            val_str = str(field.value) if field.value is not None else ""
            lines.append(f"{field.env_key}='{val_str}'")
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def load_from_dict(cls, env_values: Dict[str, str]):
        """从字典加载配置值"""
        cls.load_from_sources(env_values=env_values)

    @classmethod
    def load_from_sources(
        cls,
        env_values: Dict[str, str] | None = None,
        override_values: Dict[str, str] | None = None,
    ):
        """从基础 env 与更高优先级覆盖值加载配置。"""
        env_values = env_values or {}
        override_values = override_values or {}
        for field in cls.get_fields().values():
            # 优先级: 覆盖值 > 系统环境变量 > 传入字典 > 默认值
            val = override_values.get(field.env_key)
            if val is None:
                val = os.getenv(field.env_key)
            if val is None:
                val = env_values.get(field.env_key)

            if val is not None:
                field.value = val
            else:
                field.value = field.default

    @classmethod
    def _read_env_values(cls, env_file: str | Path | None) -> Dict[str, str]:
        if env_file is None:
            return {}
        path = Path(env_file)
        if not path.exists() or not path.is_file():
            return {}
        return dotenv.dotenv_values(path)

    @classmethod
    def _load_base_values(
        cls,
        env_path: str | Path | None,
        legacy_env_file: str | Path | None = None,
    ) -> Dict[Type['BaseEnvConfig'], Dict[str, str]]:
        if env_path is None:
            return {config_cls: {} for config_cls in cls._registry}

        source_path = Path(env_path)
        if source_path.is_file():
            env_values = cls._read_env_values(source_path)
            return {config_cls: env_values for config_cls in cls._registry}

        legacy_values = cls._read_env_values(legacy_env_file)
        base_values: Dict[Type['BaseEnvConfig'], Dict[str, str]] = {}
        for config_cls in cls._registry:
            config_path = config_cls.get_active_env_file(source_path)
            env_values = legacy_values
            if config_path.exists():
                env_values = cls._read_env_values(config_path)
            base_values[config_cls] = env_values
        return base_values

    @classmethod
    def load_all(cls, env_path: str | Path | None, legacy_env_file: str | Path | None = None):
        """加载所有已注册服务的配置"""
        base_values = cls._load_base_values(env_path, legacy_env_file=legacy_env_file)
        for config_cls in cls._registry:
            config_cls.load_from_sources(env_values=base_values.get(config_cls, {}))

    @classmethod
    def load_all_with_override(
        cls,
        env_path: str | Path | None,
        override_env_file: str | Path,
        legacy_env_file: str | Path | None = None,
    ):
        """加载默认 env，并让显式传入的 env 文件优先于系统环境变量。"""
        base_values = cls._load_base_values(env_path, legacy_env_file=legacy_env_file)
        override_values = cls._read_env_values(override_env_file)
        for config_cls in cls._registry:
            config_cls.load_from_sources(
                env_values=base_values.get(config_cls, {}),
                override_values=override_values,
            )

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
        match = cls.find_field(key)
        if match is not None:
            _, field = match
            field.value = value
            return
        # Optional: raise error or warn if key not found
        # print(f"Warning: Configuration key '{key}' not found.")

    @classmethod
    def find_field(cls, key: str):
        normalized = key.strip().lower()
        for config_cls in cls._registry:
            for name, field in config_cls.get_fields().items():
                if name.lower() == normalized or field.env_key.lower() == normalized:
                    return config_cls, field
        return None
    
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
    def get_config_by_alias(cls, alias: str) -> Type['BaseEnvConfig']:
        """根据别名获取配置类"""
        for config_cls in cls._registry:
            if alias in config_cls._aliases:
                return config_cls
        return None

    @classmethod
    def test(cls):
        """测试配置是否可用"""
        print(f"Testing {cls._title}...")
        raise NotImplementedError("Test method not implemented for this configuration.")

    @classmethod
    def save_env_file(cls, env_path: str, version: str = "0.0.0"):
        """保存当前配置到 .env 文件"""
        path = Path(env_path)
        if path.suffix == ".env":
            content = cls.generate_env_template(version)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return

        path.mkdir(parents=True, exist_ok=True)
        for config_cls in cls._registry:
            config_dir = config_cls.get_storage_dir(path)
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_cls.get_active_env_file(path)
            config_file.write_text(config_cls.render_env_file(), encoding="utf-8")

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
