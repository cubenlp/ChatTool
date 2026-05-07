"""FeishuConfig env schema."""

import json
from .base import BaseEnvConfig, EnvField


class FeishuConfig(BaseEnvConfig):
    _title = "Feishu Configuration"
    _aliases = ["feishu", "lark"]
    _storage_dir = "Feishu"

    FEISHU_APP_ID = EnvField("FEISHU_APP_ID", desc="Feishu App ID (Get from https://open.feishu.cn/app)")
    FEISHU_APP_SECRET = EnvField("FEISHU_APP_SECRET", desc="Feishu App Secret", is_sensitive=True)
    FEISHU_API_BASE = EnvField("FEISHU_API_BASE", default="https://open.feishu.cn", desc="Feishu API Base URL (Default: https://open.feishu.cn, for Lark: https://open.larksuite.com)")
    FEISHU_DEFAULT_RECEIVER_ID = EnvField("FEISHU_DEFAULT_RECEIVER_ID", desc="Default user receive_id for `chattool lark send` (optional)")
    FEISHU_DEFAULT_CHAT_ID = EnvField("FEISHU_DEFAULT_CHAT_ID", desc="Default chat_id for `chattool lark send -t chat_id` (optional)")

    FEISHU_ENCRYPT_KEY = EnvField("FEISHU_ENCRYPT_KEY", desc="Feishu Encrypt Key (Get from https://open.feishu.cn/app)")
    FEISHU_VERIFY_TOKEN = EnvField("FEISHU_VERIFY_TOKEN", desc="Feishu Verify Token (Get from https://open.feishu.cn/app)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.lark.bot import LarkBot
            bot = LarkBot()
            # Verify bot info using v3 API
            resp = bot.get_bot_info()

            if resp.code == 0:
                data = json.loads(resp.raw.content)
                bot_info = data.get("bot", {})
                app_name = bot_info.get("app_name", "Unknown")
                print(f"✅ Success! Connected to bot: {app_name}")
                print(f"   Bot Status: {'Activated' if bot_info.get('activate_status') == 2 else 'Not Activated'}")
            else:
                print(f"❌ Failed to get bot info: {resp.msg} (Code: {resp.code})")

        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["FeishuConfig"]
