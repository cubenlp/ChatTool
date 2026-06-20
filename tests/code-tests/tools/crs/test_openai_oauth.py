from datetime import datetime, timezone
import base64
import json

from chattool.tools.crs.openai_oauth import refresh_openai_oauth_token


def _make_fake_jwt(payload):
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def test_refresh_openai_oauth_token_returns_access_and_dates(monkeypatch):
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
    assert result["last_refreshed_at"] == "2026-06-21T01:02:03Z"
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


def test_refresh_openai_oauth_token_derives_issued_at_from_jwt(monkeypatch):
    fixed_now = datetime(2026, 6, 21, 1, 2, 3, tzinfo=timezone.utc)
    token = _make_fake_jwt({"iat": int(fixed_now.timestamp())})

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": token,
                "refresh_token": "new-refresh-token",
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

    monkeypatch.setattr("chattool.tools.crs.openai_oauth.httpx.Client", FakeClient)

    result = refresh_openai_oauth_token("old-refresh-token", now=fixed_now)

    assert result["access_token_issued_at"] == "2026-06-21T01:02:03Z"
