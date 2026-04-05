from .elements import BaseEnvConfig, EnvField


class HappyConfig(BaseEnvConfig):
    _title = "Happy Configuration"
    _aliases = ["happy"]
    _storage_dir = "Happy"

    HAPPY_SERVER_URL = EnvField(
        "HAPPY_SERVER_URL",
        desc="Happy server URL.",
    )
    HAPPY_WEBAPP_URL = EnvField(
        "HAPPY_WEBAPP_URL",
        desc="Happy web app URL.",
    )
    HAPPY_HOME_DIR = EnvField(
        "HAPPY_HOME_DIR",
        desc="Happy home directory (defaults to ~/.happy).",
    )
