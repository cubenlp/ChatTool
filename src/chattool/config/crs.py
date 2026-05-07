"""CRSConfig env schema."""

from .base import BaseEnvConfig, EnvField


class CRSConfig(BaseEnvConfig):
    _title = "Claude Relay Service Configuration"
    _aliases = ["crs", "claude-relay"]
    _storage_dir = "CRS"

    CRS_API_BASE = EnvField(
        "CRS_API_BASE",
        desc="Claude Relay Service root URL, for example https://crs.example.com.",
    )
    CRS_API_KEY = EnvField(
        "CRS_API_KEY",
        desc="CRS downstream API key, usually cr_..., for apiStats self queries.",
        is_sensitive=True,
    )
    CRS_USERNAME = EnvField(
        "CRS_USERNAME",
        desc="CRS admin username for /web/auth/login.",
    )
    CRS_PASSWORD = EnvField(
        "CRS_PASSWORD",
        desc="CRS admin password for /web/auth/login.",
        is_sensitive=True,
    )
    CRS_ACCESS_TOKEN = EnvField(
        "CRS_ACCESS_TOKEN",
        desc="CRS admin session token returned by /web/auth/login.",
        is_sensitive=True,
    )

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.CRS_API_BASE.value:
                print("❌ Failed: CRS_API_BASE not set")
                return

            from chattool.tools.crs.api import CRSClient

            client = CRSClient(api_base=cls.CRS_API_BASE.value)
            payload = client.models()
            count = len(payload.get("data", {}).get("all", []))
            print(f"✅ Success! CRS public models endpoint reachable ({count} models).")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["CRSConfig"]
