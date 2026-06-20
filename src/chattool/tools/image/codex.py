from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from typing import Any, Iterable

import httpx

from chattool.config import OpenAIConfig
from chattool.tools.crs.openai_oauth import refresh_openai_oauth_token

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
        base_url: str | None = None,
        host_model: str | None = None,
        image_model: str | None = None,
        aspect_ratio: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self.access_token = (access_token or "").strip() or None
        self.base_url = (
            base_url
            or OpenAIConfig.OPENAI_API_BASE.value
            or DEFAULT_BASE_URL
        )
        self.host_model = (
            host_model
            or OpenAIConfig.OPENAI_API_MODEL.value
            or DEFAULT_HOST_MODEL
        )
        self.image_model = (
            image_model
            or OpenAIConfig.OPENAI_IMAGE_MODEL.value
            or DEFAULT_IMAGE_MODEL
        )
        self.aspect_ratio = (
            aspect_ratio
            or DEFAULT_ASPECT_RATIO
        )
        self.timeout_seconds = float(
            timeout_seconds
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

    @staticmethod
    def is_datetime_expired(value: str) -> bool:
        normalized = value.strip()
        if not normalized:
            return False
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        expires_at = datetime.fromisoformat(normalized)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at.astimezone(timezone.utc)

    @staticmethod
    def _apply_refreshed_openai_token(refreshed: dict[str, Any]) -> str:
        access_token = str(refreshed.get("access_token") or "").strip()
        if not access_token:
            raise ValueError("OpenAI OAuth refresh response was missing access_token")
        OpenAIConfig.OPENAI_ACCESS_TOKEN.value = access_token
        refresh_token = str(refreshed.get("refresh_token") or "").strip()
        if refresh_token:
            OpenAIConfig.OPENAI_REFRESH_TOKEN.value = refresh_token
        expires_at = str(refreshed.get("access_token_expires_at") or "").strip()
        if expires_at:
            OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value = expires_at
        return access_token

    def _refresh_configured_access_token(self) -> str | None:
        refresh_token = (OpenAIConfig.OPENAI_REFRESH_TOKEN.value or "").strip()
        if not refresh_token:
            return None
        refreshed = refresh_openai_oauth_token(refresh_token)
        return self._apply_refreshed_openai_token(refreshed)

    def resolve_access_token(self) -> str:
        token = self.access_token
        if token:
            if self.is_token_expired(token):
                raise ValueError("OPENAI_ACCESS_TOKEN is expired")
            return token

        configured_token = (
            OpenAIConfig.OPENAI_ACCESS_TOKEN.value or ""
        ).strip()
        if configured_token:
            configured_expires_at = (
                OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value or ""
            ).strip()
            if configured_expires_at and self.is_datetime_expired(configured_expires_at):
                refreshed_token = self._refresh_configured_access_token()
                if refreshed_token:
                    return refreshed_token
                raise ValueError("OPENAI_ACCESS_TOKEN_EXPIRES_AT is expired")
            if self.is_token_expired(configured_token):
                refreshed_token = self._refresh_configured_access_token()
                if refreshed_token:
                    return refreshed_token
                raise ValueError("OPENAI_ACCESS_TOKEN is expired")
            return configured_token

        raise ValueError(
            "No usable OpenAI OAuth access token found. Set OPENAI_ACCESS_TOKEN "
            "in the OpenAI/OAI chatenv profile or pass access_token explicitly."
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
