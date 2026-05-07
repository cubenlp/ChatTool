from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from chattool.config import BaseEnvConfig, CRSConfig, OpenAIConfig
from chattool.const import CHATARCH_ENV_DIR, CHATARCH_ENV_FILE
from chattool.interaction import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs
from chattool.tools.crs.api import CRSAPIError, CRSClient, derive_crs_root_from_openai_base


LOGIN_SCHEMA = CommandSchema(
    name="crs-login",
    fields=(
        CommandField("api_base", prompt="CRS API base", required=True),
        CommandField("username", prompt="admin username", required=True),
        CommandField("password", prompt="admin password", required=True, sensitive=True),
    ),
)


def _resolve_env_path(config_cls, env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate
    profile_path = config_cls.get_profile_env_file(CHATARCH_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path
    raise click.ClickException(
        f"Config not found: {env_ref}. Use a .env file path or a saved {config_cls.get_storage_name()} profile."
    )


def _load_runtime_env(env_ref: str | None, *, openai_env_ref: str | None = None) -> None:
    if env_ref and openai_env_ref:
        raise click.ClickException("--env and --openai-env cannot be used together.")
    if env_ref:
        BaseEnvConfig.load_all_with_override(
            CHATARCH_ENV_DIR,
            override_env_file=_resolve_env_path(CRSConfig, env_ref),
        )
        return
    if openai_env_ref:
        BaseEnvConfig.load_all_with_override(
            CHATARCH_ENV_DIR,
            override_env_file=_resolve_env_path(OpenAIConfig, openai_env_ref),
        )
        CRSConfig.CRS_API_BASE.value = derive_crs_root_from_openai_base(
            OpenAIConfig.OPENAI_API_BASE.value
        )
        CRSConfig.CRS_API_KEY.value = OpenAIConfig.OPENAI_API_KEY.value
        return
    BaseEnvConfig.load_all(CHATARCH_ENV_DIR)


def _client(*, require_key: bool = False, require_token: bool = False) -> CRSClient:
    api_base = CRSConfig.CRS_API_BASE.value
    if not api_base:
        raise click.ClickException("CRS_API_BASE is required. Configure it with chatenv -t crs or pass --env.")
    api_key = CRSConfig.CRS_API_KEY.value
    access_token = CRSConfig.CRS_ACCESS_TOKEN.value
    if require_key and not api_key:
        raise click.ClickException("CRS_API_KEY is required for this command.")
    if require_token and not access_token:
        raise click.ClickException("CRS_ACCESS_TOKEN is required for this command. Run `chattool crs auth login --save` first.")
    return CRSClient(api_base=api_base, api_key=api_key, access_token=access_token)


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _fmt_int(value: Any) -> str:
    if value in (None, ""):
        return "-"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_bool(value: Any) -> str:
    if value in (True, "true", "True", "1", 1):
        return "yes"
    if value in (False, "false", "False", "0", 0):
        return "no"
    return "-" if value in (None, "") else str(value)


def _fmt_duration(seconds: Any) -> str:
    if seconds in (None, ""):
        return "-"
    try:
        remaining = max(0, int(float(seconds)))
    except (TypeError, ValueError):
        return str(seconds)
    days, rem = divmod(remaining, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def _iter_list(payload: Any) -> list[dict]:
    data = _unwrap_data(payload)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "accounts", "apiKeys", "keys", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _extract_stats_data(payload: dict) -> dict:
    data = _unwrap_data(payload)
    return data if isinstance(data, dict) else {}


def _usage_total(data: dict) -> dict:
    usage = data.get("usage") or data.get("usageStats") or {}
    if isinstance(usage, dict):
        total = usage.get("total") or usage
        return total if isinstance(total, dict) else {}
    return {}


def _echo_codex_usage(codex_usage: dict) -> None:
    if not isinstance(codex_usage, dict):
        return
    for name in ("primary", "secondary"):
        window = codex_usage.get(name)
        if not isinstance(window, dict):
            continue
        used = window.get("usedPercent") or window.get("usagePercent") or window.get("percent")
        remaining = window.get("remainingSeconds") or window.get("resetRemainingSeconds")
        label = "Primary" if name == "primary" else "Secondary"
        click.echo(f"  {label}: {used if used is not None else '-'}% used, reset in {_fmt_duration(remaining)}")


def _echo_stats(payload: dict) -> None:
    data = _extract_stats_data(payload)
    total = _usage_total(data)
    key = data.get("key") if isinstance(data.get("key"), dict) else data
    click.echo(f"API Key: {key.get('name', '-') if isinstance(key, dict) else '-'}")
    if isinstance(key, dict):
        click.echo(f"  ID: {key.get('id', '-')}")
        click.echo(f"  Active: {_fmt_bool(key.get('isActive'))}")
        permissions = key.get("permissions") or []
        if isinstance(permissions, str):
            permissions = [permissions]
        click.echo(f"  Permissions: {', '.join(permissions) if permissions else '-'}")
    click.echo("Usage:")
    click.echo(f"  Requests: {_fmt_int(total.get('requests') or total.get('requestCount'))}")
    click.echo(f"  Tokens: {_fmt_int(total.get('allTokens') or total.get('totalTokens'))}")
    click.echo(f"  Cost: {total.get('formattedCost') or total.get('cost') or '-'}")

    limits = data.get("limits") if isinstance(data.get("limits"), dict) else data
    if isinstance(limits, dict):
        daily_limit = limits.get("dailyCostLimit") or limits.get("rateLimitCost")
        daily_current = limits.get("currentDailyCost") or limits.get("dailyCost")
        window = limits.get("windowRemainingSeconds")
        if daily_limit or daily_current or window:
            click.echo("Limits:")
            click.echo(f"  Daily cost: {daily_current or 0} / {daily_limit or '-'}")
            if window:
                click.echo(f"  Window reset: {_fmt_duration(window)}")

    accounts = data.get("accounts") if isinstance(data.get("accounts"), dict) else {}
    details = accounts.get("details") if isinstance(accounts, dict) else {}
    if isinstance(details, dict):
        for platform, account in details.items():
            if not isinstance(account, dict):
                continue
            click.echo(f"Account[{platform}]: {account.get('name') or account.get('id') or '-'}")
            account_type = account.get("accountType") or account.get("type")
            if account_type:
                click.echo(f"  Type: {account_type}")
            _echo_codex_usage(account.get("codexUsage") or {})


def _echo_models(payload: dict) -> None:
    rows = _iter_list(payload)
    if not rows:
        click.echo("No model stats found.")
        return
    for row in rows:
        click.echo(
            f"- {row.get('model') or row.get('modelName') or '-'}: "
            f"requests={_fmt_int(row.get('requests') or row.get('requestCount'))}, "
            f"tokens={_fmt_int(row.get('allTokens') or row.get('totalTokens'))}, "
            f"cost={row.get('formattedCost') or row.get('cost') or '-'}"
        )


def _echo_dashboard(payload: dict) -> None:
    data = _extract_stats_data(payload)
    overview = data.get("overview") if isinstance(data.get("overview"), dict) else data
    click.echo("Dashboard:")
    for key in (
        "totalApiKeys",
        "activeApiKeys",
        "totalAccounts",
        "normalAccounts",
        "todayRequests",
        "totalRequests",
        "todayCost",
        "totalCost",
        "systemStatus",
    ):
        if key in overview:
            click.echo(f"  {key}: {overview[key]}")


def _echo_api_keys(payload: dict) -> None:
    rows = _iter_list(payload)
    if not rows:
        click.echo("No API keys found.")
        return
    for row in rows:
        click.echo(
            f"- {row.get('name') or '-'} ({row.get('id') or '-'}) "
            f"active={_fmt_bool(row.get('isActive'))} "
            f"requests={_fmt_int(row.get('requests') or row.get('totalRequests'))} "
            f"cost={row.get('formattedCost') or row.get('totalCost') or '-'}"
        )


def _echo_accounts(payload: dict) -> None:
    rows = _iter_list(payload)
    if not rows:
        click.echo("No accounts found.")
        return
    for row in rows:
        status = row.get("status") or row.get("rateLimitStatus") or "-"
        click.echo(
            f"- {row.get('name') or row.get('email') or row.get('id') or '-'} "
            f"({row.get('id') or '-'}) active={_fmt_bool(row.get('isActive'))} "
            f"schedulable={_fmt_bool(row.get('schedulable'))} status={status}"
        )
        _echo_codex_usage(row.get("codexUsage") or {})


def _run(callable_, *, json_output: bool, renderer) -> None:
    try:
        payload = callable_()
    except (CRSAPIError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        renderer(payload)


@click.group(name="crs")
def cli():
    """Claude Relay Service read-only helpers."""


@cli.group(name="auth")
def auth_group():
    """Admin authentication helpers."""


@cli.group(name="admin")
def admin_group():
    """Read-only CRS admin queries."""


@cli.command(name="stats")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--openai-env", default=None, help="Reuse an OpenAI profile by deriving CRS root from OPENAI_API_BASE.")
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def stats(env_ref, openai_env, json_output):
    """Show self usage stats for the configured CRS API key."""
    _load_runtime_env(env_ref, openai_env_ref=openai_env)
    client = _client(require_key=True)
    _run(client.user_stats, json_output=json_output, renderer=_echo_stats)


@cli.command(name="models")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--openai-env", default=None, help="Reuse an OpenAI profile by deriving CRS root from OPENAI_API_BASE.")
@click.option(
    "--period",
    default="monthly",
    show_default=True,
    type=click.Choice(["daily", "monthly", "alltime"]),
)
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def models(env_ref, openai_env, period, json_output):
    """Show per-model usage for the configured CRS API key."""
    _load_runtime_env(env_ref, openai_env_ref=openai_env)
    client = _client(require_key=True)
    _run(lambda: client.user_model_stats(period=period), json_output=json_output, renderer=_echo_models)


@auth_group.command(name="login")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--api-base", default=None, help="CRS service root URL.")
@click.option("--username", default=None, help="CRS admin username.")
@click.option("--password", default=None, help="CRS admin password.")
@click.option("--save", is_flag=True, help="Save returned token to the active CRS env file.")
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
@add_interactive_option
def login(env_ref, api_base, username, password, save, json_output, interactive):
    """Login with admin username/password and optionally save the session token."""
    _load_runtime_env(env_ref)
    inputs = resolve_command_inputs(
        schema=LOGIN_SCHEMA,
        provided={
            "api_base": api_base or CRSConfig.CRS_API_BASE.value,
            "username": username or CRSConfig.CRS_USERNAME.value,
            "password": password or CRSConfig.CRS_PASSWORD.value,
        },
        interactive=interactive,
        usage="Usage: chattool crs auth login --api-base URL --username USER --password PASS [-i|-I]",
    )
    client = CRSClient(api_base=inputs["api_base"])
    try:
        payload = client.login(username=inputs["username"], password=inputs["password"])
    except (CRSAPIError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    token = payload.get("token") if isinstance(payload, dict) else None
    if save and token:
        CRSConfig.CRS_API_BASE.value = inputs["api_base"]
        CRSConfig.CRS_USERNAME.value = inputs["username"]
        CRSConfig.CRS_PASSWORD.value = inputs["password"]
        CRSConfig.CRS_ACCESS_TOKEN.value = token
        target_path = CRSConfig.get_active_env_file(CHATARCH_ENV_DIR)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(CRSConfig.render_env_file(), encoding="utf-8")
    if json_output:
        _echo_json(payload)
        return
    click.echo(f"Login: {payload.get('username') or inputs['username']}")
    if payload.get("expiresIn"):
        click.echo(f"Expires in: {_fmt_duration(payload.get('expiresIn'))}")
    if save and token:
        click.echo(f"Saved token: {CRSConfig.get_active_env_file(CHATARCH_ENV_DIR)}")


@auth_group.command(name="whoami")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def whoami(env_ref, json_output):
    """Show current admin session user."""
    _load_runtime_env(env_ref)
    client = _client(require_token=True)
    _run(client.whoami, json_output=json_output, renderer=lambda payload: _echo_json(payload.get("user", payload)))


@admin_group.command(name="dashboard")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def dashboard(env_ref, json_output):
    """Show admin dashboard summary."""
    _load_runtime_env(env_ref)
    client = _client(require_token=True)
    _run(client.dashboard, json_output=json_output, renderer=_echo_dashboard)


@admin_group.command(name="api-keys")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option("--page", default=1, type=int, show_default=True)
@click.option("--limit", default=20, type=int, show_default=True)
@click.option("--search", default=None, help="Filter API keys by CRS search text.")
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def api_keys(env_ref, page, limit, search, json_output):
    """List CRS API keys with admin token."""
    _load_runtime_env(env_ref)
    client = _client(require_token=True)
    _run(lambda: client.api_keys(page=page, limit=limit, search=search), json_output=json_output, renderer=_echo_api_keys)


@admin_group.command(name="accounts")
@click.option("--env", "env_ref", default=None, help="CRS .env path or saved CRS profile.")
@click.option(
    "--type",
    "account_type",
    default="openai",
    show_default=True,
    type=click.Choice(["openai", "claude", "openai-responses", "gemini"]),
)
@click.option("--json-output", is_flag=True, help="Output raw JSON.")
def accounts(env_ref, account_type, json_output):
    """List CRS upstream accounts with admin token."""
    _load_runtime_env(env_ref)
    client = _client(require_token=True)
    _run(lambda: client.accounts(account_type=account_type), json_output=json_output, renderer=_echo_accounts)
