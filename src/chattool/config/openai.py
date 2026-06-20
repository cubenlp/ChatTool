"""OpenAIConfig env schema."""

import json
from .base import BaseEnvConfig, EnvField


class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    _storage_dir = "OpenAI"

    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API (with suffix /v1).")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-5.5", desc="The default model name")
    OPENAI_ACCESS_TOKEN = EnvField(
        "OPENAI_ACCESS_TOKEN",
        desc="OpenAI OAuth access token for OAuth-backed capabilities.",
        is_sensitive=True,
    )
    OPENAI_REFRESH_TOKEN = EnvField(
        "OPENAI_REFRESH_TOKEN",
        desc="OpenAI OAuth refresh token for OAuth-backed capabilities.",
        is_sensitive=True,
    )
    OPENAI_OAUTH_BASE_URL = EnvField(
        "OPENAI_OAUTH_BASE_URL",
        default="https://auth.openai.com",
        desc="OpenAI OAuth auth server base URL used to refresh access tokens.",
    )
    OPENAI_ACCESS_TOKEN_EXPIRES_AT = EnvField(
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT",
        desc="UTC ISO timestamp when the OpenAI OAuth access token expires.",
    )
    OPENAI_IMAGE_MODEL = EnvField(
        "OPENAI_IMAGE_MODEL",
        default="gpt-image-2-medium",
        desc="Default OpenAI image model preset.",
    )

    @classmethod
    def _parse_responses_stream_event(cls, line: str):
        if not line.startswith("data:"):
            return None
        payload = line.removeprefix("data:").strip()
        if not payload or payload == "[DONE]":
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    @classmethod
    def _validate_responses_stream(cls, response) -> str:
        for line in response.iter_lines():
            event = cls._parse_responses_stream_event(line)
            if not event:
                continue
            event_type = event.get("type")
            if event_type in ("response.failed", "error"):
                error = event.get("error") or event.get("response", {}).get("error")
                raise RuntimeError(error or event_type)
            if event_type == "response.output_text.delta" and event.get("delta"):
                return "generated"
            if event_type == "response.completed":
                return "completed"
            if event_type in ("response.incomplete", "response.cancelled"):
                raise RuntimeError(event_type)
        raise RuntimeError("Responses stream ended before output or completion event")

    @classmethod
    def _test_responses_api(cls):
        import httpx

        api_base = (cls.OPENAI_API_BASE.value or "").rstrip("/")
        api_key = cls.OPENAI_API_KEY.value
        model = cls.OPENAI_API_MODEL.value
        if not api_base:
            raise ValueError("OPENAI_API_BASE not set")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        if not model:
            raise ValueError("OPENAI_API_MODEL not set")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "input": [{"role": "user", "content": "hi"}],
            "max_output_tokens": 8,
            "stream": True,
        }
        with httpx.Client(timeout=30) as client:
            with client.stream(
                "POST", f"{api_base}/responses", json=data, headers=headers
            ) as response:
                response.raise_for_status()
                return cls._validate_responses_stream(response)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            # Prefer the Responses API: current CRS/Codex-style OpenAI endpoints
            # expose models such as gpt-5.x through /responses rather than
            # /chat/completions. Use streaming for proxies that require it,
            # consume enough events to prove generation works, and do not print
            # response chunks because they may include context.
            try:
                result = cls._test_responses_api()
                print(f"✅ Success! Responses API {result}.")
                return
            except Exception as responses_error:
                try:
                    from chattool.llm.chattype import Chat

                    chat = Chat(messages=[{"role": "user", "content": "hi"}])
                    resp = chat.get_response(max_tokens=5)
                    print(f"✅ Success! Chat Completions API: {resp.content}")
                except Exception as chat_error:
                    raise RuntimeError(
                        "Responses API failed: "
                        f"{responses_error}; Chat Completions API failed: {chat_error}"
                    ) from chat_error
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["OpenAIConfig"]
