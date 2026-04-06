from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

import click

from chattool.config import BaseEnvConfig, FeishuConfig
from chattool.config.source_chain import split_config_sources
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    prompt_sensitive_value,
    prompt_text_value,
    resolve_interactive_mode,
    resolve_value,
)
from chattool.setup.nodejs import (
    _detect_nodejs_runtime,
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_lark_cli")


def _mask_secret(value):
    if not value:
        return ""
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"


def _get_lark_cli_config_dir() -> Path:
    override = os.getenv("LARKSUITE_CLI_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".lark-cli"


def _get_lark_cli_config_path() -> Path:
    return _get_lark_cli_config_dir() / "config.json"


def _snapshot_feishu_values() -> dict[str, str | None]:
    return {
        "app_id": FeishuConfig.FEISHU_APP_ID.value,
        "app_secret": FeishuConfig.FEISHU_APP_SECRET.value,
        "api_base": FeishuConfig.FEISHU_API_BASE.value,
    }


def _load_saved_feishu_values() -> dict[str, str | None]:
    current_values = _snapshot_feishu_values()
    try:
        BaseEnvConfig.load_all(CHATTOOL_ENV_DIR, legacy_env_file=CHATTOOL_ENV_FILE)
        return _snapshot_feishu_values()
    finally:
        _restore_feishu_values(current_values)


def _restore_feishu_values(values: dict[str, str | None]) -> None:
    FeishuConfig.FEISHU_APP_ID.value = values.get("app_id")
    FeishuConfig.FEISHU_APP_SECRET.value = values.get("app_secret")
    FeishuConfig.FEISHU_API_BASE.value = values.get("api_base")


def _resolve_feishu_env_path(env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate

    profile_path = FeishuConfig.get_profile_env_file(CHATTOOL_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path

    raise click.ClickException(
        f"未找到 Feishu 配置: {env_ref}。可传入 .env 文件路径，或 Feishu 类型下保存的 profile 名称。"
    )


def _load_feishu_values_from_env_ref(env_ref: str) -> dict[str, str | None]:
    current_values = _snapshot_feishu_values()
    try:
        env_path = _resolve_feishu_env_path(env_ref)
        BaseEnvConfig.load_all_with_override(
            CHATTOOL_ENV_DIR,
            override_env_file=env_path,
            legacy_env_file=CHATTOOL_ENV_FILE,
        )
        return _snapshot_feishu_values()
    finally:
        _restore_feishu_values(current_values)


def _infer_brand(api_base: str | None, explicit_brand: str | None = None) -> str:
    if explicit_brand:
        return explicit_brand
    normalized = (api_base or "").strip().lower()
    if "larksuite" in normalized:
        return "lark"
    return "feishu"


def _load_existing_lark_cli_config(config_path: Path) -> dict[str, str | None]:
    existing = {
        "app_id": None,
        "brand": None,
        "user_name": None,
        "user_open_id": None,
    }
    if not config_path.exists():
        return existing

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return existing

    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        return existing

    app = apps[0]
    if not isinstance(app, dict):
        return existing

    existing["app_id"] = app.get("appId")
    existing["brand"] = app.get("brand")

    users = app.get("users")
    if isinstance(users, list) and users:
        user = users[0]
        if isinstance(user, dict):
            existing["user_name"] = user.get("userName")
            existing["user_open_id"] = user.get("userOpenId")
    return existing


def _load_existing_lark_cli_users(config_path: Path) -> list[dict]:
    if not config_path.exists():
        return []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        return []

    app = apps[0]
    if not isinstance(app, dict):
        return []

    users = app.get("users")
    if not isinstance(users, list):
        return []

    return [user for user in users if isinstance(user, dict)]


def _write_lark_cli_file_secret_config(
    config_path: Path,
    app_id: str,
    app_secret: str,
    brand: str,
) -> Path:
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    secret_path = config_dir / "app-secret.txt"
    secret_path.write_text(f"{app_secret}\n", encoding="utf-8")
    secret_path.chmod(0o600)

    config_payload = {
        "apps": [
            {
                "appId": app_id,
                "appSecret": {"source": "file", "id": str(secret_path)},
                "brand": brand,
                "users": _load_existing_lark_cli_users(config_path),
            }
        ]
    }
    config_path.write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    config_path.chmod(0o600)
    return secret_path


def _run_lark_cli_command(
    args: list[str], input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    runtime = _detect_nodejs_runtime()
    if runtime.get("source") == "nvm":
        quoted = " ".join(shlex.quote(str(arg)) for arg in ["lark-cli", *args])
        command = (
            'export NVM_DIR="$HOME/.nvm" && '
            '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
            f"{quoted}"
        )
        return subprocess.run(
            ["bash", "-c", command],
            input=input_text,
            capture_output=True,
            text=True,
        )

    return subprocess.run(
        ["lark-cli", *args],
        input=input_text,
        capture_output=True,
        text=True,
    )


def setup_lark_cli(
    app_id=None, app_secret=None, brand=None, env_ref=None, interactive=None
):
    config_dir = _get_lark_cli_config_dir()
    config_path = _get_lark_cli_config_path()
    existing = _load_existing_lark_cli_config(config_path)
    saved_feishu = _load_saved_feishu_values()
    env_values, typed_env_values = split_config_sources(
        FeishuConfig,
        CHATTOOL_ENV_DIR,
        legacy_env_file=CHATTOOL_ENV_FILE,
    )
    env_config = _load_feishu_values_from_env_ref(env_ref) if env_ref else {}
    logger.info("Start lark-cli setup")

    if isinstance(app_id, str) and not app_id.strip():
        app_id = None
    if isinstance(app_secret, str) and not app_secret.strip():
        app_secret = None
    if isinstance(brand, str):
        brand = brand.strip().lower() or None

    app_id = resolve_value(
        app_id,
        env_config.get("app_id"),
        existing.get("app_id"),
        saved_feishu.get("app_id"),
        env_values.get("FEISHU_APP_ID"),
        typed_env_values.get("FEISHU_APP_ID"),
    )
    app_secret = resolve_value(
        app_secret,
        env_config.get("app_secret"),
        existing.get("app_secret"),
        saved_feishu.get("app_secret"),
        env_values.get("FEISHU_APP_SECRET"),
        typed_env_values.get("FEISHU_APP_SECRET"),
    )
    if not brand:
        if env_config.get("api_base"):
            brand = _infer_brand(env_config.get("api_base"))
        elif existing.get("brand"):
            brand = existing.get("brand")
        elif saved_feishu.get("api_base"):
            brand = _infer_brand(saved_feishu.get("api_base"))
        elif env_values.get("FEISHU_API_BASE"):
            brand = _infer_brand(env_values.get("FEISHU_API_BASE"))
        elif typed_env_values.get("FEISHU_API_BASE"):
            brand = _infer_brand(typed_env_values.get("FEISHU_API_BASE"))
        else:
            brand = "feishu"

    missing_required = not (app_id and app_secret)
    has_existing_config = config_path.exists()
    usage = (
        "Usage: chattool setup lark-cli [--app-id <value>] [--app-secret <value>] "
        "[--brand feishu|lark] [-e <feishu-env>] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=(missing_required or has_existing_config),
        )
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    try:
        abort_if_missing_without_tty(
            missing_required=missing_required,
            interactive=interactive,
            can_prompt=can_prompt,
            message="Missing required arguments and no TTY is available for interactive prompts.",
            usage=usage,
        )
    except click.Abort:
        logger.error("Missing required arguments and no TTY available")
        raise

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    if need_prompt:
        app_id = prompt_text_value("lark-cli app_id", app_id)
        if app_id == BACK_VALUE:
            return

        app_secret = prompt_sensitive_value(
            "lark-cli app_secret", app_secret, _mask_secret
        )
        if app_secret == BACK_VALUE:
            return

        brand = prompt_text_value(
            "lark-cli brand (feishu/lark)", brand, fallback="feishu"
        )
        if brand == BACK_VALUE:
            return

    if not (app_id and app_secret):
        logger.error("Missing app_id or app_secret")
        click.echo("Missing app_id or app_secret.", err=True)
        raise click.Abort()

    if brand not in {"feishu", "lark"}:
        logger.error("Invalid brand value")
        click.echo("Invalid brand. Expected `feishu` or `lark`.", err=True)
        raise click.Abort()

    if should_install_global_npm_package(
        "@larksuite/cli",
        "lark-cli",
        interactive=interactive,
        can_prompt=can_prompt,
    ):
        logger.info("Installing lark-cli with npm")
        install_result = run_npm_command(["install", "-g", "@larksuite/cli@latest"])
        if install_result.returncode != 0:
            logger.error("Failed to install lark-cli")
            click.echo("Failed to install lark-cli.", err=True)
            if install_result.stderr:
                click.echo(install_result.stderr.strip(), err=True)
            raise click.Abort()

    logger.info("Initializing lark-cli config")
    init_result = _run_lark_cli_command(
        [
            "config",
            "init",
            "--app-id",
            str(app_id),
            "--app-secret-stdin",
            "--brand",
            str(brand),
        ],
        input_text=f"{app_secret}\n",
    )
    if init_result.returncode != 0:
        stderr_text = (init_result.stderr or "").strip()
        stdout_text = (init_result.stdout or "").strip()
        combined_output = "\n".join(part for part in [stderr_text, stdout_text] if part)
        if "keychain unavailable" in combined_output:
            logger.warning(
                "lark-cli keychain unavailable, falling back to file secret reference"
            )
            secret_path = _write_lark_cli_file_secret_config(
                config_path=config_path,
                app_id=str(app_id),
                app_secret=str(app_secret),
                brand=str(brand),
            )
            click.echo(
                "lark-cli keychain unavailable; wrote config with file secret reference."
            )
            click.echo(f"Secret file: {secret_path}")
        else:
            logger.error("Failed to initialize lark-cli config")
            click.echo("Failed to initialize lark-cli config.", err=True)
            if stderr_text:
                click.echo(stderr_text, err=True)
            elif stdout_text:
                click.echo(stdout_text, err=True)
            raise click.Abort()

    click.echo("lark-cli setup completed.")
    click.echo(f"Config dir: {config_dir}")
    click.echo(f"Config file: {config_path}")
    click.echo(
        f"ChatTool Feishu env: {CHATTOOL_ENV_DIR / FeishuConfig.get_storage_name() / '.env'}"
    )
    if env_ref:
        click.echo(f"Reused ChatTool Feishu config: {env_ref}")
    else:
        click.echo("Reused ChatTool Feishu config: saved active Feishu config")
    click.echo("Next step: lark-cli auth login --recommend")
    click.echo("Optional Skills install: npx skills add larksuite/cli -y -g")
