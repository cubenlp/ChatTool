from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from chattool.config import BaseEnvConfig, OpenAIConfig  # type: ignore[attr-defined]
from chattool.const import CHATARCH_ENV_DIR
from chattool.tools.crs.openai_oauth import (
    build_openai_oauth_refresh_result,
    build_openai_oauth_status,
    refresh_openai_oauth_token,
    save_openai_oauth_token_data,
)

config: dict[str, Any] = {
    "token": None,
    "env_dir": CHATARCH_ENV_DIR,
    "oauth_base_url": None,
    "timeout_seconds": 20.0,
}

app = FastAPI(
    title="ChatTool OAuth Token Service",
    description="Local auth service for OAuth token status, refresh, and access-token retrieval.",
    version="0.1.0",
)


class OAuthConfigRequest(BaseModel):
    access_token: str | None = Field(default=None)
    refresh_token: str | None = Field(default=None)
    oauth_base_url: str | None = Field(default=None)
    access_token_expires_at: str | None = Field(default=None)


class OAuthRefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None)
    oauth_base_url: str | None = Field(default=None)
    timeout_seconds: float | None = Field(default=None)
    save: bool = Field(default=True)


def _env_dir() -> Path:
    return Path(config.get("env_dir") or CHATARCH_ENV_DIR)


def _active_openai_env_file() -> Path:
    return OpenAIConfig.get_active_env_file(_env_dir())


def _load_openai_env() -> None:
    if _active_openai_env_file().exists():
        BaseEnvConfig.load_all(_env_dir())


def _configured_oauth_base_url(override: str | None = None) -> str:
    value = (
        override
        or config.get("oauth_base_url")
        or OpenAIConfig.OPENAI_OAUTH_BASE_URL.value
        or "https://auth.openai.com"
    )
    return str(value).strip().rstrip("/")


def _service_token() -> str | None:
    value = config.get("token")
    return str(value) if value else None


async def require_service_token(
    x_chattool_token: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> str:
    expected = _service_token()
    if not expected:
        raise HTTPException(status_code=403, detail="Service token is not configured")
    provided = x_chattool_token
    if not provided and authorization:
        prefix = "Bearer "
        if authorization.startswith(prefix):
            provided = authorization[len(prefix):]
    if provided != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing service token")
    return str(provided)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_expired_or_missing(expires_at: str | None) -> bool:
    parsed = _parse_iso(expires_at)
    if parsed is None:
        return True
    return parsed <= datetime.now(timezone.utc)


def _save_current_openai_values(target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(OpenAIConfig.render_env_file(), encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/oauth/status")
def oauth_status(_: str = Depends(require_service_token)) -> dict[str, str]:
    _load_openai_env()
    return build_openai_oauth_status(env_file=_active_openai_env_file())


@app.post("/oauth/config")
def oauth_config(
    request: OAuthConfigRequest,
    _: str = Depends(require_service_token),
) -> dict[str, str]:
    _load_openai_env()
    if request.access_token is not None:
        OpenAIConfig.OPENAI_ACCESS_TOKEN.value = request.access_token
    if request.refresh_token is not None:
        OpenAIConfig.OPENAI_REFRESH_TOKEN.value = request.refresh_token
    if request.oauth_base_url is not None:
        OpenAIConfig.OPENAI_OAUTH_BASE_URL.value = request.oauth_base_url.strip().rstrip("/")
    elif config.get("oauth_base_url"):
        OpenAIConfig.OPENAI_OAUTH_BASE_URL.value = _configured_oauth_base_url()
    if request.access_token_expires_at is not None:
        OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value = request.access_token_expires_at
    target_path = _active_openai_env_file()
    _save_current_openai_values(target_path)
    return build_openai_oauth_status(env_file=target_path)


@app.post("/oauth/refresh")
def oauth_refresh(
    request: OAuthRefreshRequest | None = None,
    _: str = Depends(require_service_token),
) -> dict[str, Any]:
    _load_openai_env()
    request = request or OAuthRefreshRequest()
    refresh_token = (request.refresh_token or OpenAIConfig.OPENAI_REFRESH_TOKEN.value or "").strip()
    if not refresh_token:
        raise HTTPException(status_code=400, detail="OPENAI_REFRESH_TOKEN is required")
    oauth_base_url = _configured_oauth_base_url(request.oauth_base_url)
    timeout_seconds = request.timeout_seconds or float(config.get("timeout_seconds") or 20.0)
    try:
        token_data = refresh_openai_oauth_token(
            refresh_token,
            base_url=oauth_base_url,
            timeout_seconds=timeout_seconds,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    target_path = _active_openai_env_file()
    if request.save:
        save_openai_oauth_token_data(
            token_data=token_data,
            oauth_base_url=oauth_base_url,
            target_path=target_path,
        )
    return build_openai_oauth_refresh_result(
        token_data=token_data,
        oauth_base_url=oauth_base_url,
        saved=request.save,
        env_file=target_path if request.save else None,
    )


@app.get("/oauth/access-token")
def oauth_access_token(_: str = Depends(require_service_token)) -> dict[str, Any]:
    _load_openai_env()
    access_token = (OpenAIConfig.OPENAI_ACCESS_TOKEN.value or "").strip()
    expires_at = OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value
    refreshed = False
    if not access_token or _is_expired_or_missing(expires_at):
        refresh_token = (OpenAIConfig.OPENAI_REFRESH_TOKEN.value or "").strip()
        if not refresh_token:
            raise HTTPException(status_code=400, detail="No valid access token and no refresh token configured")
        oauth_base_url = _configured_oauth_base_url()
        try:
            token_data = refresh_openai_oauth_token(
                refresh_token,
                base_url=oauth_base_url,
                timeout_seconds=float(config.get("timeout_seconds") or 20.0),
            )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        save_openai_oauth_token_data(
            token_data=token_data,
            oauth_base_url=oauth_base_url,
            target_path=_active_openai_env_file(),
        )
        access_token = str(token_data.get("access_token") or "")
        expires_at = str(token_data.get("access_token_expires_at") or "")
        refreshed = True
    return {
        "access_token": access_token,
        "access_token_expires_at": expires_at,
        "refreshed": refreshed,
    }


@click.command(name="oauth")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host.")
@click.option("--port", default=8787, show_default=True, type=int, help="Bind port.")
@click.option("--token", default=None, help="Service token required by protected endpoints.")
@click.option("--env-dir", default=None, help="ChatArch env directory. Defaults to the active ChatTool env dir.")
@click.option("--oauth-base-url", default=None, help="Default OAuth auth server base URL.")
@click.option("--timeout", "timeout_seconds", default=20.0, type=float, show_default=True)
@click.option("--dry-run", is_flag=True, help="Print resolved server settings without starting uvicorn.")
def oauth(host: str, port: int, token: str | None, env_dir: str | None, oauth_base_url: str | None, timeout_seconds: float, dry_run: bool) -> None:
    """Run the local OAuth token service."""
    config["token"] = token
    config["env_dir"] = Path(env_dir).expanduser() if env_dir else CHATARCH_ENV_DIR
    config["oauth_base_url"] = oauth_base_url
    config["timeout_seconds"] = timeout_seconds
    click.echo(f"OAuth service: http://{host}:{port}")
    click.echo(f"Env dir: {config['env_dir']}")
    click.echo(f"OAuth base: {_configured_oauth_base_url()}")
    click.echo(f"Service token: {'configured' if token else 'missing'}")
    if dry_run:
        return
    if not token:
        raise click.ClickException("--token is required unless --dry-run is used.")
    import uvicorn

    uvicorn.run(app, host=host, port=port)
