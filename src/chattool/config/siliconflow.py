"""SiliconFlowConfig env schema."""

from .base import BaseEnvConfig, EnvField


class SiliconFlowConfig(BaseEnvConfig):
    _title = "SiliconFlow Configuration"
    _aliases = ["siliconflow"]
    _storage_dir = "SiliconFlow"

    SILICONFLOW_API_KEY = EnvField("SILICONFLOW_API_KEY", desc="SiliconFlow API Key. See https://cloud.siliconflow.cn/account/ak", is_sensitive=True)
    SILICONFLOW_MODEL_ID = EnvField("SILICONFLOW_MODEL_ID", default="black-forest-labs/FLUX.1-schnell", desc="Default Image Model ID. Use `chattool image siliconflow list-models` to see available models.")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.SILICONFLOW_API_KEY.value:
                print("❌ Failed: SILICONFLOW_API_KEY not set")
                return

            # Simple test to check if key is valid (requires network)
            # For now, just print success if key is present
            print(f"✅ Success! Key configured.")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["SiliconFlowConfig"]
