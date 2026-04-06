from .elements import BaseEnvConfig, EnvField


class GitHubConfig(BaseEnvConfig):
    _title = "GitHub Configuration"
    _aliases = ["github", "gh"]
    _storage_dir = "GitHub"

    GITHUB_ACCESS_TOKEN = EnvField(
        "GITHUB_ACCESS_TOKEN", desc="GitHub Personal Access Token", is_sensitive=True
    )

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.GITHUB_ACCESS_TOKEN.value:
                print("❌ Failed: GITHUB_ACCESS_TOKEN not set")
                return
            print("✅ Config loaded.")
        except Exception as e:
            print(f"❌ Failed: {e}")
