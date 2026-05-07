"""TongyiConfig env schema."""

from .base import BaseEnvConfig, EnvField


class TongyiConfig(BaseEnvConfig):
    _title = "Tongyi Wanxiang Configuration"
    _aliases = ["tongyi", "dashscope"]
    _storage_dir = "Tongyi"

    DASHSCOPE_API_KEY = EnvField("DASHSCOPE_API_KEY", desc="Aliyun DashScope API Key. See https://bailian.console.aliyun.com/cn-beijing/?tab=model#/api-key", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            # 简单验证 key 是否存在
            if not cls.DASHSCOPE_API_KEY.value:
                print("❌ Failed: DASHSCOPE_API_KEY not set")
                return

            # 尝试导入并调用
            from chattool.tools.image.tongyi import TongyiImageGenerator
            # 注意：这里我们不真正生成图片，因为那会消耗额度且较慢，
            # 我们可以尝试初始化 Client，如果 key 格式不对通常会在使用时报错。
            # 由于 Tongyi 的 SDK 也是惰性的，这里主要检查 import 和 key 存在。
            client = TongyiImageGenerator(api_key=cls.DASHSCOPE_API_KEY.value)
            print(f"✅ Success! Client initialized with key: {cls.DASHSCOPE_API_KEY.mask_value()}")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["TongyiConfig"]
