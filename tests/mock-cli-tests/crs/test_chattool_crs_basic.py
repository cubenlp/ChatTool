from pathlib import Path

import pytest

from chattool.client.main import cli
import chattool.tools.crs.cli as crs_cli
from chattool.config import CRSConfig


pytestmark = pytest.mark.mock_cli


class FakeClient:
    calls = []

    def __init__(self, *, api_base, api_key=None, access_token=None, timeout=30):
        self.api_base = api_base
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout
        FakeClient.calls.append(("init", api_base, api_key, access_token))

    def user_stats(self):
        FakeClient.calls.append(("user_stats", self.api_key))
        return {
            "success": True,
            "data": {
                "id": "key-1",
                "name": "openai",
                "isActive": "true",
                "permissions": ["openai"],
                "usage": {"total": {"requests": 12, "allTokens": 3456, "formattedCost": "$1.23"}},
                "accounts": {
                    "details": {
                        "openai": {
                            "id": "acct-1",
                            "accountType": "dedicated",
                            "codexUsage": {
                                "primary": {"usedPercent": 70, "remainingSeconds": 8940},
                                "secondary": {"usedPercent": 77, "remainingSeconds": 583200},
                            },
                        }
                    }
                },
            },
        }

    def user_model_stats(self, *, period="monthly"):
        FakeClient.calls.append(("user_model_stats", period))
        return {"success": True, "data": [{"model": "gpt-5.5", "requests": 7, "allTokens": 8000, "formattedCost": "$0.45"}]}

    def login(self, *, username, password):
        FakeClient.calls.append(("login", username, password))
        return {"success": True, "token": "session-token-123", "expiresIn": 3600, "username": username}

    def whoami(self):
        FakeClient.calls.append(("whoami", self.access_token))
        return {"success": True, "user": {"username": "admin"}}

    def dashboard(self):
        FakeClient.calls.append(("dashboard", self.access_token))
        return {"success": True, "data": {"totalApiKeys": 2, "totalAccounts": 3, "systemStatus": "healthy"}}

    def api_keys(self, *, page=1, limit=20, search=None):
        FakeClient.calls.append(("api_keys", page, limit, search, self.access_token))
        return {"success": True, "data": {"items": [{"id": "key-1", "name": "openai", "isActive": "true", "totalRequests": 5}]}}

    def accounts(self, *, account_type):
        FakeClient.calls.append(("accounts", account_type, self.access_token))
        return {"success": True, "data": [{"id": "acct-1", "name": "openai-account", "isActive": True, "schedulable": True}]}


@pytest.fixture(autouse=True)
def fake_crs_config(monkeypatch, tmp_path):
    FakeClient.calls = []
    monkeypatch.setattr(crs_cli, "CRSClient", FakeClient)
    monkeypatch.setattr(crs_cli, "_load_runtime_env", lambda env_ref=None, *, openai_env_ref=None: None)
    monkeypatch.setattr(crs_cli, "CHATTOOL_ENV_DIR", tmp_path / "envs")
    monkeypatch.setattr(crs_cli, "CHATTOOL_ENV_FILE", tmp_path / ".env")
    CRSConfig.CRS_API_BASE.value = "https://crs.example.com"
    CRSConfig.CRS_API_KEY.value = "cr_test"
    CRSConfig.CRS_USERNAME.value = "admin"
    CRSConfig.CRS_PASSWORD.value = "secret"
    CRSConfig.CRS_ACCESS_TOKEN.value = "admin-token"
    yield


def test_chattool_crs_help_commands(runner):
    result = runner.invoke(cli, ["crs", "--help"])
    assert result.exit_code == 0
    for command in ["auth", "stats", "models", "admin"]:
        assert command in result.output

    result = runner.invoke(cli, ["crs", "admin", "--help"])
    assert result.exit_code == 0
    for command in ["dashboard", "api-keys", "accounts"]:
        assert command in result.output


def test_chattool_crs_stats_reads_env_and_renders_usage(runner):
    result = runner.invoke(cli, ["crs", "stats"], catch_exceptions=False)

    assert result.exit_code == 0
    assert ("init", "https://crs.example.com", "cr_test", "admin-token") in FakeClient.calls
    assert ("user_stats", "cr_test") in FakeClient.calls
    assert "API Key: openai" in result.output
    assert "Requests: 12" in result.output
    assert "Tokens: 3,456" in result.output
    assert "$1.23" in result.output
    assert "Primary: 70% used" in result.output
    assert "Secondary: 77% used" in result.output


def test_chattool_crs_models_forwards_period(runner):
    result = runner.invoke(cli, ["crs", "models", "--period", "daily"], catch_exceptions=False)

    assert result.exit_code == 0
    assert ("user_model_stats", "daily") in FakeClient.calls
    assert "gpt-5.5" in result.output
    assert "requests=7" in result.output


def test_chattool_crs_auth_login_save_writes_token(runner, tmp_path):
    result = runner.invoke(
        cli,
        [
            "crs",
            "auth",
            "login",
            "--api-base",
            "https://crs.example.com",
            "--username",
            "admin",
            "--password",
            "secret",
            "--save",
            "-I",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "session-token-123" not in result.output
    env_file = CRSConfig.get_active_env_file(tmp_path / "envs")
    assert env_file.exists()
    content = env_file.read_text()
    assert "CRS_ACCESS_TOKEN='session-token-123'" in content


def test_chattool_crs_admin_read_only_commands(runner):
    result = runner.invoke(cli, ["crs", "admin", "dashboard"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "totalApiKeys: 2" in result.output
    assert ("dashboard", "admin-token") in FakeClient.calls

    result = runner.invoke(cli, ["crs", "admin", "api-keys", "--page", "2", "--limit", "3"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "openai" in result.output
    assert ("api_keys", 2, 3, None, "admin-token") in FakeClient.calls

    result = runner.invoke(cli, ["crs", "admin", "accounts", "--type", "openai"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "openai-account" in result.output
    assert ("accounts", "openai", "admin-token") in FakeClient.calls


def test_chattool_crs_auth_login_errors_with_no_interaction(runner):
    CRSConfig.CRS_API_BASE.value = ""
    CRSConfig.CRS_USERNAME.value = ""
    CRSConfig.CRS_PASSWORD.value = ""

    result = runner.invoke(cli, ["crs", "auth", "login", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: api_base" in result.output
