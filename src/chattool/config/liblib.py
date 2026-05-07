"""LiblibConfig env schema."""

from .base import BaseEnvConfig, EnvField


class LiblibConfig(BaseEnvConfig):
    _title = "LiblibAI Configuration"
    _aliases = ["liblib"]
    _storage_dir = "Liblib"

    LIBLIB_MODEL_ID = EnvField("LIBLIB_MODEL_ID", desc="LiblibAI Model ID. Use `chattool image liblib list-models` to get available models.")
    LIBLIB_ACCESS_KEY = EnvField("LIBLIB_ACCESS_KEY", desc="LiblibAI Access Key. See https://www.liblib.art/apis", is_sensitive=True)
    LIBLIB_SECRET_KEY = EnvField("LIBLIB_SECRET_KEY", desc="LiblibAI Secret Key. See https://www.liblib.art/apis", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            if not cls.LIBLIB_ACCESS_KEY.value or not cls.LIBLIB_SECRET_KEY.value:
                print("❌ Failed: LIBLIB_ACCESS_KEY or LIBLIB_SECRET_KEY not set")
                return

            from chattool.tools.image.liblib import LiblibImageGenerator
            client = LiblibImageGenerator(
                access_key=cls.LIBLIB_ACCESS_KEY.value,
                secret_key=cls.LIBLIB_SECRET_KEY.value
            )
            print(f"✅ Success! Client initialized.")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["LiblibConfig"]
