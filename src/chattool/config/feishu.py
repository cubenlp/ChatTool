"""FeishuConfig compatibility re-export.

The shared Feishu/Lark field schema lives in :mod:`chatenv.configs`. ChatTool
re-exports that canonical class and attaches ChatTool-specific connectivity
helpers when ChatTool is imported.
"""

import json

from chatenv.configs import FeishuConfig


def _test(cls):
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


FeishuConfig.test = classmethod(_test)

__all__ = ["FeishuConfig"]
