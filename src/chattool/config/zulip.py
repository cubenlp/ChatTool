"""ZulipConfig env schema."""

from .base import BaseEnvConfig, EnvField


class ZulipConfig(BaseEnvConfig):
    _title = "Zulip Configuration"
    _aliases = ["zulip"]
    _storage_dir = "Zulip"

    ZULIP_BOT_EMAIL = EnvField("ZULIP_BOT_EMAIL", desc="Zulip Bot Email")
    ZULIP_BOT_API_KEY = EnvField("ZULIP_BOT_API_KEY", desc="Zulip Bot API Key", is_sensitive=True)
    ZULIP_SITE = EnvField("ZULIP_SITE", desc="Zulip Site URL")
    ZULIP_NEWS_STREAMS = EnvField("ZULIP_NEWS_STREAMS", desc="Comma-separated stream names for news summary")
    ZULIP_NEWS_TOPICS = EnvField("ZULIP_NEWS_TOPICS", desc="Comma-separated topic names for news summary")
    ZULIP_NEWS_SINCE_HOURS = EnvField("ZULIP_NEWS_SINCE_HOURS", default="24", desc="Default hours for news window")
    ZULIP_NEWS_PER_STREAM = EnvField("ZULIP_NEWS_PER_STREAM", default="200", desc="Default per-stream fetch limit for news")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.zulip.client import ZulipClient
            client = ZulipClient()
            profile = client.get_profile()
            print(f"✅ Success! Authenticated as: {profile.get('email')} ({profile.get('full_name')})")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["ZulipConfig"]
