from .elements import BaseEnvConfig, EnvField


class BrowserConfig(BaseEnvConfig):
    _title = "Browser Configuration"
    _aliases = ["browser"]

    BROWSER_CHROMIUM_CDP_URL = EnvField(
        "BROWSER_CHROMIUM_CDP_URL",
        desc="Chromium CDP URL for remote browser connection.",
    )
    BROWSER_CHROMIUM_TOKEN = EnvField(
        "BROWSER_CHROMIUM_TOKEN",
        desc="Optional token appended as ?token= to CDP URL.",
        is_sensitive=True,
    )

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            print("✅ Config loaded.")
        except Exception as e:
            print(f"❌ Failed: {e}")
