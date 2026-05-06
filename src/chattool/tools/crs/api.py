from __future__ import annotations

from urllib.parse import urlparse, urlunparse

import httpx


class CRSAPIError(RuntimeError):
    """Raised when CRS returns an HTTP or application-level error."""


def derive_crs_root_from_openai_base(api_base: str | None) -> str | None:
    if not api_base:
        return None
    value = api_base.strip().rstrip("/")
    for suffix in ("/openai/v1", "/v1"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return value or None


class CRSClient:
    def __init__(
        self,
        *,
        api_base: str,
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: float = 30,
    ):
        if not api_base:
            raise ValueError("CRS_API_BASE is required")
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.api_base}/{path.lstrip('/')}"

    def _admin_headers(self) -> dict[str, str]:
        if not self.access_token:
            raise ValueError("CRS_ACCESS_TOKEN is required")
        return {"Authorization": f"Bearer {self.access_token}"}

    def _request(self, method: str, path: str, **kwargs):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, self._url(path), **kwargs)
        except httpx.HTTPError as exc:
            raise CRSAPIError(str(exc)) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text}

        if response.status_code >= 400:
            message = payload.get("message") or payload.get("error") or response.text
            raise CRSAPIError(f"HTTP {response.status_code}: {message}")
        if isinstance(payload, dict) and payload.get("success") is False:
            message = payload.get("message") or payload.get("error") or "CRS request failed"
            raise CRSAPIError(str(message))
        return payload

    def models(self) -> dict:
        return self._request("GET", "/apiStats/api/models")

    def user_stats(self) -> dict:
        if not self.api_key:
            raise ValueError("CRS_API_KEY is required")
        return self._request("POST", "/apiStats/api/user-stats", json={"apiKey": self.api_key})

    def user_model_stats(self, *, period: str = "monthly") -> dict:
        if not self.api_key:
            raise ValueError("CRS_API_KEY is required")
        return self._request(
            "POST",
            "/apiStats/api/user-model-stats",
            json={"apiKey": self.api_key, "period": period},
        )

    def login(self, *, username: str, password: str) -> dict:
        return self._request(
            "POST",
            "/web/auth/login",
            json={"username": username, "password": password},
        )

    def whoami(self) -> dict:
        return self._request("GET", "/web/auth/user", headers=self._admin_headers())

    def dashboard(self) -> dict:
        return self._request("GET", "/admin/dashboard", headers=self._admin_headers())

    def api_keys(self, *, page: int = 1, limit: int = 20, search: str | None = None) -> dict:
        params = {"page": page, "pageSize": limit}
        if search:
            params["search"] = search
        return self._request(
            "GET", "/admin/api-keys", headers=self._admin_headers(), params=params
        )

    def accounts(self, *, account_type: str) -> dict:
        endpoint_map = {
            "openai": "/admin/openai-accounts",
            "claude": "/admin/claude-accounts",
            "openai-responses": "/admin/openai-responses-accounts",
            "gemini": "/admin/gemini-accounts",
        }
        endpoint = endpoint_map[account_type]
        return self._request("GET", endpoint, headers=self._admin_headers())
