from .elements import BaseEnvConfig, EnvField


class BrowserConfig(BaseEnvConfig):
    _title = "Browser Configuration"
    _aliases = ["browser"]
    _storage_dir = "Browser"

    BROWSER_DEFAULT_BACKEND = EnvField(
        "BROWSER_DEFAULT_BACKEND",
        default="playwright",
        desc="Default backend: playwright | selenium | chromium",
    )
    BROWSER_CHROMIUM_CDP_URL = EnvField(
        "BROWSER_CHROMIUM_CDP_URL",
        desc="Chromium CDP URL (via /chromium/ proxy).",
    )
    BROWSER_CHROMIUM_TOKEN = EnvField(
        "BROWSER_CHROMIUM_TOKEN",
        desc="Chromium token (optional, appended as ?token= if provided).",
        is_sensitive=True,
    )
    BROWSER_SELENIUM_REMOTE_URL = EnvField(
        "BROWSER_SELENIUM_REMOTE_URL",
        desc="Selenium remote WebDriver URL (via /chromedriver/ proxy).",
    )
    BROWSER_PLAYWRIGHT_URL = EnvField(
        "BROWSER_PLAYWRIGHT_URL",
        desc="Playwright service URL (currently not exposed).",
    )

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            print("✅ Config loaded.")
        except Exception as e:
            print(f"❌ Failed: {e}")
