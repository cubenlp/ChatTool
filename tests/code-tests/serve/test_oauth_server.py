from fastapi.testclient import TestClient

from chattool.config import OpenAIConfig
import chattool.serve.oauth as oauth_serve


def _client(tmp_path):
    oauth_serve.config["token"] = "svc-token"
    oauth_serve.config["env_dir"] = tmp_path / "envs"
    oauth_serve.config["oauth_base_url"] = "https://oauth.example.test"
    return TestClient(oauth_serve.app)


def _headers():
    return {"X-ChatTool-Token": "svc-token"}


def test_oauth_server_health_is_public(tmp_path):
    client = _client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_oauth_server_status_requires_service_token_and_masks_secrets(tmp_path):
    client = _client(tmp_path)
    OpenAIConfig.OPENAI_ACCESS_TOKEN.value = "access-secret"
    OpenAIConfig.OPENAI_REFRESH_TOKEN.value = "refresh-secret"
    OpenAIConfig.OPENAI_OAUTH_BASE_URL.value = "https://oauth.example.test"
    OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value = "2026-06-21T02:02:03Z"

    unauth = client.get("/oauth/status")
    response = client.get("/oauth/status", headers=_headers())

    assert unauth.status_code == 403
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "present"
    assert data["refresh_token"] == "present"
    assert data["oauth_base_url"] == "https://oauth.example.test"
    assert data["access_token_expires_at"] == "2026-06-21T02:02:03Z"
    assert "access-secret" not in str(data)
    assert "refresh-secret" not in str(data)


def test_oauth_server_config_saves_openai_token_metadata(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/oauth/config",
        headers=_headers(),
        json={
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
            "oauth_base_url": "https://oauth.example.test",
            "access_token_expires_at": "2026-06-21T02:02:03Z",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "present"
    assert data["refresh_token"] == "present"
    assert "access-secret" not in str(data)
    env_file = OpenAIConfig.get_active_env_file(tmp_path / "envs")
    content = env_file.read_text()
    assert "OPENAI_ACCESS_TOKEN='access-secret'" in content
    assert "OPENAI_REFRESH_TOKEN='refresh-secret'" in content
    assert "OPENAI_OAUTH_BASE_URL='https://oauth.example.test'" in content


def test_oauth_server_refresh_saves_without_leaking_tokens(tmp_path, monkeypatch):
    client = _client(tmp_path)
    OpenAIConfig.OPENAI_REFRESH_TOKEN.value = "old-refresh-secret"
    calls = []

    def fake_refresh(refresh_token, *, base_url=None, timeout_seconds=20.0, **kwargs):
        calls.append((refresh_token, base_url, timeout_seconds))
        return {
            "access_token": "new-access-secret",
            "refresh_token": "new-refresh-secret",
            "access_token_expires_at": "2026-06-21T02:02:03Z",
        }

    monkeypatch.setattr(oauth_serve, "refresh_openai_oauth_token", fake_refresh)

    response = client.post("/oauth/refresh", headers=_headers(), json={"save": True})

    assert response.status_code == 200
    assert calls == [("old-refresh-secret", "https://oauth.example.test", 20.0)]
    data = response.json()
    assert data["access_token"] == "present"
    assert data["refresh_token"] == "present"
    assert data["saved"] is True
    assert "new-access-secret" not in str(data)
    assert "new-refresh-secret" not in str(data)


def test_oauth_server_access_token_returns_secret_only_to_authenticated_client(tmp_path, monkeypatch):
    client = _client(tmp_path)
    OpenAIConfig.OPENAI_ACCESS_TOKEN.value = "expired-access-secret"
    OpenAIConfig.OPENAI_REFRESH_TOKEN.value = "old-refresh-secret"
    OpenAIConfig.OPENAI_OAUTH_BASE_URL.value = "https://oauth.example.test"
    OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value = "2000-01-01T00:00:00Z"

    def fake_refresh(refresh_token, *, base_url=None, timeout_seconds=20.0, **kwargs):
        return {
            "access_token": "fresh-access-secret",
            "refresh_token": "fresh-refresh-secret",
            "access_token_expires_at": "2026-06-21T02:02:03Z",
        }

    monkeypatch.setattr(oauth_serve, "refresh_openai_oauth_token", fake_refresh)

    unauth = client.get("/oauth/access-token")
    response = client.get("/oauth/access-token", headers=_headers())

    assert unauth.status_code == 403
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "fresh-access-secret",
        "access_token_expires_at": "2026-06-21T02:02:03Z",
        "refreshed": True,
    }
