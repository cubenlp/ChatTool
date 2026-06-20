from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

OPENAI_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
OPENAI_CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
OPENAI_OAUTH_SCOPE = "openid profile email"


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def refresh_openai_oauth_token(
    refresh_token: str,
    *,
    client_id: str = OPENAI_CODEX_CLIENT_ID,
    token_url: str = OPENAI_OAUTH_TOKEN_URL,
    scope: str = OPENAI_OAUTH_SCOPE,
    timeout_seconds: float = 20.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Exchange an OpenAI OAuth refresh token for a fresh access token.

    Returns normalized token metadata suitable for OpenAI/OAI chatenv storage.
    The refresh token itself is opaque; the authoritative expiry comes from
    the OAuth token endpoint's ``expires_in`` response.
    """
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise ValueError("refresh_token is required")

    refreshed_at = now or datetime.now(timezone.utc)
    timeout = httpx.Timeout(max(5.0, float(timeout_seconds)))
    with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}) as client:
        response = client.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "scope": scope,
            },
        )

    if response.status_code != 200:
        raise RuntimeError(f"OpenAI OAuth token refresh failed with status {response.status_code}")

    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise RuntimeError("OpenAI OAuth refresh response was missing access_token")

    next_refresh = payload.get("refresh_token")
    if not isinstance(next_refresh, str) or not next_refresh.strip():
        next_refresh = refresh_token

    expires_in = int(payload.get("expires_in") or 3600)
    expires_at = refreshed_at + timedelta(seconds=expires_in)

    result: dict[str, Any] = {
        "access_token": access_token.strip(),
        "refresh_token": next_refresh.strip(),
        "access_token_expires_at": _iso_z(expires_at),
    }
    id_token = payload.get("id_token")
    if isinstance(id_token, str) and id_token.strip():
        result["id_token"] = id_token.strip()
    return result
