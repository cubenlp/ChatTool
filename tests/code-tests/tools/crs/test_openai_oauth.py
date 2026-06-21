from datetime import datetime, timezone
from unittest.mock import patch

from chattool.config import OpenAIConfig
from chattool.tools.crs.openai_oauth import (
    build_openai_oauth_status,
    refresh_openai_oauth_token,
    save_openai_oauth_token_data,
)


def test_refresh_openai_oauth_token_returns_access_and_expiry(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
                "id_token": "new-id-token",
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, headers, data):
            captured["url"] = url
            captured["headers"] = headers
            captured["data"] = data
            return FakeResponse()

    fixed_now = datetime(2026, 6, 21, 1, 2, 3, tzinfo=timezone.utc)
    monkeypatch.setattr("chattool.tools.crs.openai_oauth.httpx.Client", FakeClient)

    result = refresh_openai_oauth_token(
        "old-refresh-token",
        now=fixed_now,
    )

    assert captured["url"] == "https://auth.openai.com/oauth/token"
    assert captured["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert captured["data"]["grant_type"] == "refresh_token"
    assert captured["data"]["refresh_token"] == "old-refresh-token"
    assert captured["data"]["client_id"] == "app_EMoamEEZ73f0CkXaXp7hrann"
    assert captured["data"]["scope"] == "openid profile email"
    assert result["access_token"] == "new-access-token"
    assert result["refresh_token"] == "new-refresh-token"
    assert result["id_token"] == "new-id-token"
    assert result["access_token_expires_at"] == "2026-06-21T02:02:03Z"


def test_refresh_openai_oauth_token_keeps_old_refresh_when_rotation_not_returned(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "new-access-token",
                "expires_in": 60,
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, headers, data):
            return FakeResponse()

    fixed_now = datetime(2026, 6, 21, 1, 2, 3, tzinfo=timezone.utc)
    monkeypatch.setattr("chattool.tools.crs.openai_oauth.httpx.Client", FakeClient)

    result = refresh_openai_oauth_token("old-refresh-token", now=fixed_now)

    assert result["access_token"] == "new-access-token"
    assert result["refresh_token"] == "old-refresh-token"
    assert result["access_token_expires_at"] == "2026-06-21T01:03:03Z"


def test_refresh_openai_oauth_token_uses_configured_base_url(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "new-access-token",
                "expires_in": 60,
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, headers, data):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setattr("chattool.tools.crs.openai_oauth.httpx.Client", FakeClient)
    with patch.object(
        OpenAIConfig.OPENAI_OAUTH_BASE_URL,
        "value",
        "https://oauth.example.test",
    ):
        refresh_openai_oauth_token("old-refresh-token")

    assert captured["url"] == "https://oauth.example.test/oauth/token"


def test_build_openai_oauth_status_never_returns_secret_values(tmp_path):
    env_file = tmp_path / "OpenAI" / ".env"
    with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", "access-secret"), \
         patch.object(OpenAIConfig.OPENAI_REFRESH_TOKEN, "value", "refresh-secret"), \
         patch.object(OpenAIConfig.OPENAI_OAUTH_BASE_URL, "value", "https://oauth.example.test"), \
         patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT, "value", "2026-06-21T02:02:03Z"):
        status = build_openai_oauth_status(env_file=env_file)

    assert status == {
        "access_token": "present",
        "refresh_token": "present",
        "oauth_base_url": "https://oauth.example.test",
        "access_token_expires_at": "2026-06-21T02:02:03Z",
        "env_file": str(env_file),
    }
    assert "access-secret" not in str(status)
    assert "refresh-secret" not in str(status)


def test_save_openai_oauth_token_data_writes_openai_env(tmp_path):
    target = tmp_path / "envs" / "OpenAI" / ".env"

    save_openai_oauth_token_data(
        token_data={
            "access_token": "new-access-secret",
            "refresh_token": "new-refresh-secret",
            "access_token_expires_at": "2026-06-21T02:02:03Z",
        },
        oauth_base_url="https://oauth.example.test",
        target_path=target,
    )

    content = target.read_text()
    assert "OPENAI_ACCESS_TOKEN='new-access-secret'" in content
    assert "OPENAI_REFRESH_TOKEN='new-refresh-secret'" in content
    assert "OPENAI_ACCESS_TOKEN_EXPIRES_AT='2026-06-21T02:02:03Z'" in content
    assert "OPENAI_OAUTH_BASE_URL='https://oauth.example.test'" in content
