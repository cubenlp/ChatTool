"""PollinationsConfig env schema."""

from .base import BaseEnvConfig, EnvField


class PollinationsConfig(BaseEnvConfig):
    _title = "Pollinations Configuration"
    _aliases = ["pollinations", "poll"]
    _storage_dir = "Pollinations"

    POLLINATIONS_API_KEY = EnvField("POLLINATIONS_API_KEY", desc="Pollinations API Key (from enter.pollinations.ai)", is_sensitive=True)
    POLLINATIONS_MODEL_ID = EnvField("POLLINATIONS_MODEL_ID", default="flux", desc="Default Pollinations model ID.")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            print("✅ Config loaded.")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["PollinationsConfig"]
