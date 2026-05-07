"""TPLinkConfig env schema."""

from .base import BaseEnvConfig, EnvField


class TPLinkConfig(BaseEnvConfig):
    _title = "TP-Link Router Configuration"
    _aliases = ["tplink", "tplogin"]
    _storage_dir = "TPLink"

    TPLOGIN_URL = EnvField("TPLOGIN_URL", default="http://192.168.1.1", desc="TP-Link Router Login URL")
    TPLOGIN_AUTH_PASSWORD = EnvField("TPLOGIN_AUTH_PASSWORD", desc="TP-Link Router Password", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.TPLOGIN_AUTH_PASSWORD.value:
                print("❌ Failed: TPLOGIN_AUTH_PASSWORD not set")
                return

            from chattool.tools.tplogin import TPLogin
            client = TPLogin()
            stok = client.login()
            if stok:
                print(f"✅ Success! Login successful. Stok: {stok}")
            else:
                print("❌ Failed: Login failed")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["TPLinkConfig"]
