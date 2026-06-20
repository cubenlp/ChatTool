from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any, Iterable

import httpx

from chattool.config import OpenAICodexConfig

from .base import ImageGenerator

DEFAULT_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_HOST_MODEL = "gpt-5.4"
DEFAULT_IMAGE_MODEL = "gpt-image-2-medium"
DEFAULT_ASPECT_RATIO = "square"
DEFAULT_TIMEOUT_SECONDS = 300.0

IMAGE_MODEL_CONFIG = {
    "gpt-image-2-low": {
        "quality": "low",
        "size": {
            "landscape": "1536x1024",
            "square": "1024x1024",
            "portrait": "1024x1536",
        },
    },
    "gpt-image-2-medium": {
        "quality": "medium",
        "size": {
            "landscape": "1536x1024",
            "square": "1024x1024",
            "portrait": "1024x1536",
        },
    },
    "gpt-image-2-high": {
        "quality": "high",
        "size": {
            "landscape": "1536x1024",
            "square": "1024x1024",
            "portrait": "1024x1536",
        },
    },
}


class CodexImageGenerator(ImageGenerator):
    """Generate images through the ChatGPT/Codex OAuth-backed Responses API."""

    def __init__(
        self,
        access_token: str | None = None,
        auth_json_path: str | Path | None = None,
        base_url: str | None = None,
        host_model: str | None = None,
        image_model: str | None = None,
        aspect_ratio: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self.access_token = (access_token or "").strip() or None
        self.auth_json_path = (
            Path(auth_json_path).expanduser() if auth_json_path else None
        )
        self.base_url = (
            base_url
            or OpenAICodexConfig.OPENAI_CODEX_BASE_URL.value
            or DEFAULT_BASE_URL
        )
        self.host_model = (
            host_model
            or OpenAICodexConfig.OPENAI_CODEX_HOST_MODEL.value
            or DEFAULT_HOST_MODEL
        )
        self.image_model = (
            image_model
            or OpenAICodexConfig.OPENAI_CODEX_IMAGE_MODEL.value
            or DEFAULT_IMAGE_MODEL
        )
        self.aspect_ratio = (
            aspect_ratio
            or OpenAICodexConfig.OPENAI_CODEX_ASPECT_RATIO.value
            or DEFAULT_ASPECT_RATIO
        )
        self.timeout_seconds = float(
            timeout_seconds
            or OpenAICodexConfig.OPENAI_CODEX_TIMEOUT.value
            or DEFAULT_TIMEOUT_SECONDS
        )
        self._validate_options(self.image_model, self.aspect_ratio)

    @staticmethod
    def _validate_options(image_model: str, aspect_ratio: str) -> None:
        if image_model not in IMAGE_MODEL_CONFIG:
            raise ValueError(f"Unsupported Codex image model: {image_model}")
        if aspect_ratio not in IMAGE_MODEL_CONFIG[image_model]["size"]:
            raise ValueError(f"Unsupported Codex aspect ratio: {aspect_ratio}")

    @staticmethod
    def decode_jwt_claims(token: str) -> dict[str, Any]:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        try:
            payload = base64.urlsafe_b64decode(payload_b64)
            return json.loads(payload)
        except Exception:
            return {}

    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        claims = cls.decode_jwt_claims(token)
        exp = claims.get("exp")
        return bool(exp and time.time() > float(exp))

    def auth_json_candidates(self) -> Iterable[Path]:
        if self.auth_json_path:
            yield self.auth_json_path
            return
        configured_path = (OpenAICodexConfig.OPENAI_CODEX_AUTH_JSON.value or "").strip()
        if configured_path:
            yield Path(configured_path).expanduser()
            return
        yield Path.home() / ".hermes" / "auth.json"

    def read_token_from_auth_json(self) -> str | None:
        for path in self.auth_json_candidates():
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            pool = data.get("credential_pool", {}).get("openai-codex")
            if isinstance(pool, list):
                for entry in pool:
                    token = str((entry or {}).get("access_token") or "").strip()
                    if token and not self.is_token_expired(token):
                        return token

            providers = data.get("providers", {})
            codex = providers.get("openai-codex") if isinstance(providers, dict) else None
            if isinstance(codex, dict):
                token = str(
                    ((codex.get("tokens") or {}).get("access_token")) or ""
                ).strip()
                if token and not self.is_token_expired(token):
                    return token
        return None

    def resolve_access_token(self) -> str:
        token = self.access_token
        if token:
            if self.is_token_expired(token):
                raise ValueError("OPENAI_CODEX_ACCESS_TOKEN is expired")
            return token

        configured_token = (
            OpenAICodexConfig.OPENAI_CODEX_ACCESS_TOKEN.value or ""
        ).strip()
        if configured_token:
            if self.is_token_expired(configured_token):
                raise ValueError("OPENAI_CODEX_ACCESS_TOKEN is expired")
            return configured_token

        token = self.read_token_from_auth_json()
        if token:
            return token

        raise ValueError(
            "No usable Codex access token found. Set OPENAI_CODEX_ACCESS_TOKEN, "
            "or point OPENAI_CODEX_AUTH_JSON to a Hermes auth.json with a valid "
            "openai-codex login."
        )

    @classmethod
    def codex_headers(cls, access_token: str) -> dict[str, str]:
        headers = {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "chattool/7.x (CodexImageGenerator)",
            "originator": "codex_cli_rs",
        }
        claims = cls.decode_jwt_claims(access_token)
        auth_claim = claims.get("https://api.openai.com/auth")
        acct_id = auth_claim.get("chatgpt_account_id") if isinstance(auth_claim, dict) else None
        if isinstance(acct_id, str) and acct_id:
            headers["ChatGPT-Account-ID"] = acct_id
        return headers

    def build_payload(
        self,
        prompt: str,
        *,
        host_model: str,
        image_model: str,
        aspect_ratio: str,
        background: str = "opaque",
        partial_images: int = 1,
    ) -> dict[str, Any]:
        self._validate_options(image_model, aspect_ratio)
        model_config = IMAGE_MODEL_CONFIG[image_model]
        return {
            "model": host_model,
            "store": False,
            "instructions": (
                "You are an assistant that must fulfill image generation "
                "requests by using the image_generation tool when provided."
            ),
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }
            ],
            "tools": [
                {
                    "type": "image_generation",
                    "model": "gpt-image-2",
                    "size": model_config["size"][aspect_ratio],
                    "quality": model_config["quality"],
                    "output_format": "png",
                    "background": background,
                    "partial_images": partial_images,
                }
            ],
            "tool_choice": {
                "type": "allowed_tools",
                "mode": "required",
                "tools": [{"type": "image_generation"}],
            },
            "stream": True,
        }

    @staticmethod
    def iter_sse_json(response: httpx.Response) -> Iterable[dict[str, Any]]:
        event_name: str | None = None
        data_lines: list[str] = []

        def flush() -> dict[str, Any] | None:
            nonlocal event_name, data_lines
            if not data_lines:
                event_name = None
                return None

            raw = "\n".join(data_lines).strip()
            event = event_name
            event_name = None
            data_lines = []

            if not raw or raw == "[DONE]":
                return None

            payload = json.loads(raw)
            if isinstance(payload, dict) and event and "type" not in payload:
                payload["type"] = event
            return payload

        for line in response.iter_lines():
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            line = str(line)
            if line == "":
                payload = flush()
                if payload is not None:
                    yield payload
                continue
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].lstrip())

        payload = flush()
        if payload is not None:
            yield payload

    @classmethod
    def extract_image_b64(cls, value: Any) -> str | None:
        found: str | None = None
        if isinstance(value, dict):
            if value.get("type") == "image_generation_call":
                result = value.get("result")
                if isinstance(result, str) and result:
                    found = result
            partial = value.get("partial_image_b64")
            if isinstance(partial, str) and partial:
                found = partial
            for child in value.values():
                nested = cls.extract_image_b64(child)
                if nested:
                    found = nested
        elif isinstance(value, list):
            for child in value:
                nested = cls.extract_image_b64(child)
                if nested:
                    found = nested
        return found

    def request_image_b64(
        self,
        access_token: str,
        *,
        prompt: str,
        host_model: str,
        image_model: str,
        aspect_ratio: str,
        timeout_seconds: float,
        background: str = "opaque",
        partial_images: int = 1,
    ) -> str:
        headers = self.codex_headers(access_token)
        payload = self.build_payload(
            prompt,
            host_model=host_model,
            image_model=image_model,
            aspect_ratio=aspect_ratio,
            background=background,
            partial_images=partial_images,
        )
        timeout = httpx.Timeout(
            timeout_seconds,
            connect=30.0,
            read=timeout_seconds,
            write=30.0,
            pool=30.0,
        )
        latest_b64: str | None = None
        with httpx.Client(timeout=timeout, headers=headers) as client:
            with client.stream(
                "POST", f"{self.base_url.rstrip('/')}/responses", json=payload
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    exc.response.read()
                    snippet = exc.response.text[:800]
                    raise RuntimeError(
                        "Codex Responses API returned HTTP "
                        f"{exc.response.status_code}: {snippet}"
                    ) from exc
                for event in self.iter_sse_json(response):
                    found = self.extract_image_b64(event)
                    if found:
                        latest_b64 = found

        if not latest_b64:
            raise RuntimeError(
                "Codex response contained no image_generation_call result"
            )
        return latest_b64

    def generate(self, prompt: str, **kwargs) -> bytes:
        access_token = (kwargs.pop("access_token", None) or "").strip() or None
        host_model = kwargs.pop("host_model", None) or self.host_model
        image_model = kwargs.pop("image_model", None) or self.image_model
        aspect_ratio = kwargs.pop("aspect_ratio", None) or self.aspect_ratio
        timeout_seconds = float(
            kwargs.pop("timeout_seconds", None) or self.timeout_seconds
        )
        background = kwargs.pop("background", "opaque")
        partial_images = int(kwargs.pop("partial_images", 1))
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise ValueError(f"Unsupported Codex image kwargs: {unknown}")

        self._validate_options(image_model, aspect_ratio)
        token = access_token or self.resolve_access_token()
        image_b64 = self.request_image_b64(
            token,
            prompt=prompt,
            host_model=host_model,
            image_model=image_model,
            aspect_ratio=aspect_ratio,
            timeout_seconds=timeout_seconds,
            background=background,
            partial_images=partial_images,
        )
        return base64.b64decode(image_b64)

    def get_models(self) -> list[dict[str, Any]]:
        models = []
        for model_id, meta in IMAGE_MODEL_CONFIG.items():
            models.append(
                {
                    "id": model_id,
                    "quality": meta["quality"],
                    "sizes": meta["size"],
                }
            )
        return models
