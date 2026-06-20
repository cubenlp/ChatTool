"""OpenAICodexConfig env schema."""

from __future__ import annotations

import time

from .base import BaseEnvConfig, EnvField


class OpenAICodexConfig(BaseEnvConfig):
    _title = "OpenAI Codex Image Configuration"
    _aliases = ["openai-codex", "codex-image"]
    _storage_dir = "OpenAICodex"

    OPENAI_CODEX_ACCESS_TOKEN = EnvField(
        "OPENAI_CODEX_ACCESS_TOKEN",
        desc="ChatGPT/Codex OAuth access token used for image generation.",
        is_sensitive=True,
    )
    OPENAI_CODEX_AUTH_JSON = EnvField(
        "OPENAI_CODEX_AUTH_JSON",
        desc="Optional auth.json path. Defaults to ~/.hermes/auth.json when unset.",
    )
    OPENAI_CODEX_BASE_URL = EnvField(
        "OPENAI_CODEX_BASE_URL",
        default="https://chatgpt.com/backend-api/codex",
        desc="Codex backend base URL used for the Responses API bridge.",
    )
    OPENAI_CODEX_HOST_MODEL = EnvField(
        "OPENAI_CODEX_HOST_MODEL",
        default="gpt-5.4",
        desc="Host chat model used to invoke the image_generation tool.",
    )
    OPENAI_CODEX_IMAGE_MODEL = EnvField(
        "OPENAI_CODEX_IMAGE_MODEL",
        default="gpt-image-2-medium",
        desc="Default image model preset: gpt-image-2-low/medium/high.",
    )
    OPENAI_CODEX_ASPECT_RATIO = EnvField(
        "OPENAI_CODEX_ASPECT_RATIO",
        default="square",
        desc="Default image aspect ratio: square, landscape, or portrait.",
    )
    OPENAI_CODEX_TIMEOUT = EnvField(
        "OPENAI_CODEX_TIMEOUT",
        default="300",
        desc="Request timeout in seconds for Codex image generation.",
    )

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.tools.image.codex import CodexImageGenerator

            generator = CodexImageGenerator(
                access_token=cls.OPENAI_CODEX_ACCESS_TOKEN.value or None,
                auth_json_path=cls.OPENAI_CODEX_AUTH_JSON.value or None,
                base_url=cls.OPENAI_CODEX_BASE_URL.value or None,
                host_model=cls.OPENAI_CODEX_HOST_MODEL.value or None,
                image_model=cls.OPENAI_CODEX_IMAGE_MODEL.value or None,
                aspect_ratio=cls.OPENAI_CODEX_ASPECT_RATIO.value or None,
                timeout_seconds=float(cls.OPENAI_CODEX_TIMEOUT.value or 300),
            )
            token = generator.resolve_access_token()
            claims = generator.decode_jwt_claims(token)
            exp = claims.get("exp")
            if exp:
                remaining = max(0, int(float(exp) - time.time()))
                print(
                    "✅ Success! Codex access token resolved "
                    f"({remaining}s remaining)."
                )
            else:
                print("✅ Success! Codex access token resolved.")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["OpenAICodexConfig"]
