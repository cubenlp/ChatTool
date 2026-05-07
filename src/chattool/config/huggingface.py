"""HuggingFaceConfig env schema."""

from .base import BaseEnvConfig, EnvField


class HuggingFaceConfig(BaseEnvConfig):
    _title = "Hugging Face Configuration"
    _aliases = ["hf", "huggingface"]
    _storage_dir = "HuggingFace"

    HUGGINGFACE_HUB_TOKEN = EnvField("HUGGINGFACE_HUB_TOKEN", desc="Hugging Face User Access Token. See https://huggingface.co/settings/tokens", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.HUGGINGFACE_HUB_TOKEN.value:
                print("❌ Failed: HUGGINGFACE_HUB_TOKEN not set")
                return

            from chattool.tools.image.huggingface import HuggingFaceImageGenerator
            client = HuggingFaceImageGenerator(api_key=cls.HUGGINGFACE_HUB_TOKEN.value)
            print(f"✅ Success! Client initialized with token: {cls.HUGGINGFACE_HUB_TOKEN.mask_value()}")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["HuggingFaceConfig"]
