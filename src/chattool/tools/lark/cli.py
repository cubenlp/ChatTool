"""
chattool lark — 飞书机器人 CLI 工具

Commands:
    chattool lark send       发送消息
    chattool lark info       获取机器人信息
    chattool lark listen     启动 WebSocket 监听（调试模式）
    chattool lark chat       启动交互式 AI 对话
"""
import os
import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import click
from collections import defaultdict

from chattool.cli_warnings import install_cli_warning_filters
from chattool.config import BaseEnvConfig, FeishuConfig
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE

install_cli_warning_filters()

@click.group()
def cli():
    """飞书机器人工具"""
    pass


def _resolve_env_path(env_ref: str) -> Path:
    """Resolve an env file path, config directory, or saved Feishu profile name."""
    candidate = Path(env_ref).expanduser()
    if candidate.exists():
        return candidate

    profile_path = FeishuConfig.get_profile_env_file(CHATTOOL_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path

    raise click.ClickException(
        f"未找到配置文件: {env_ref}。可传入配置目录 / .env 文件路径，或 Feishu 类型下保存的 profile 名称。"
    )


def _load_runtime_env(env_ref: str | None) -> Path | None:
    """Load runtime config from the specified env file or profile."""
    if not env_ref:
        return None

    env_path = _resolve_env_path(env_ref)
    BaseEnvConfig.load_all(str(env_path))
    return env_path


def _get_bot():
    """Lazy-init a LarkBot from loaded config or environment variables."""
    from chattool.tools.lark.bot import LarkBot

    try:
        return LarkBot()
    except Exception as e:
        click.secho(f"初始化失败: {e}", fg="red", err=True)
        click.echo(
            "请确认已设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET，"
            f"或通过 -e/--env 指定配置目录 / 配置文件（默认读取 {CHATTOOL_ENV_DIR / FeishuConfig.get_storage_name() / '.env'}）。",
            err=True,
        )
        sys.exit(1)


def _print_lark_error(action: str, resp) -> bool:
    """Print a standardized Lark API error."""
    if getattr(resp, "success", None) and resp.success():
        return False
    if getattr(resp, "code", 0) == 0:
        return False
    click.secho(f"❌ {action}失败: code={resp.code}  msg={resp.msg}", fg="red")
    return True


def _resolve_receiver_and_text(
    receiver: str | None,
    text: str | None,
    *,
    has_structured_content: bool,
) -> tuple[str | None, str | None]:
    """Resolve receiver/text with FEISHU_DEFAULT_RECEIVER_ID fallback."""
    default_receiver = FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value or None

    if receiver and (text or has_structured_content):
        return receiver, text

    if receiver and not text and not has_structured_content and default_receiver:
        # Allow `chattool lark send "hello"` when a default receiver is configured.
        return default_receiver, receiver

    if not receiver and default_receiver:
        return default_receiver, text

    return receiver, text


def _has_default_receiver() -> bool:
    return bool(FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value)


def _resolve_message_receiver(receiver: str | None) -> str | None:
    return receiver or FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value or None


def _read_append_file_paragraphs(path: str | None) -> list[str]:
    """Read a local text/markdown file and convert it into plain-text paragraphs."""
    if not path:
        return []

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    if file_path.suffix.lower() == ".md":
        return _markdown_to_paragraphs(content)
    return [line.strip() for line in content.splitlines() if line.strip()]


def _strip_markdown_inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1 \2", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    return re.sub(r"\s+", " ", text).strip()


def _markdown_to_paragraphs(content: str) -> list[str]:
    paragraphs = []
    current = []
    in_code_block = False

    def flush():
        if current:
            paragraph = " ".join(part for part in current if part).strip()
            if paragraph:
                paragraphs.append(paragraph)
            current.clear()

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush()
            in_code_block = not in_code_block
            continue
        if in_code_block:
            if stripped:
                paragraphs.append(stripped)
            continue
        if not stripped:
            flush()
            continue

        stripped = re.sub(r"^\s{0,3}#{1,6}\s+", "", stripped)
        stripped = re.sub(r"^\s*>\s?", "", stripped)
        stripped = re.sub(r"^\s*[-*+]\s+", "• ", stripped)
        stripped = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", stripped)
        stripped = _strip_markdown_inline(stripped)
        if not stripped:
            continue

        if stripped.startswith("• ") or re.match(r"^\d+\.\s", stripped):
            flush()
            paragraphs.append(stripped)
            continue

        current.append(stripped)

    flush()
    return paragraphs


def _append_doc_paragraphs(bot, document_id, paragraphs, block_id=None, index=None, batch_size=20):
    return bot.append_doc_texts_safe(
        document_id=document_id,
        texts=paragraphs,
        block_id=block_id,
        index=index,
        batch_size=batch_size,
    )


def _response_json(resp) -> dict:
    raw = getattr(getattr(resp, "raw", None), "content", None)
    if raw is None:
        return {}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _print_json(payload: dict | list) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json_file(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parse_markdown_blocks(content: str):
    from chattool.tools.lark.markdown_blocks import parse_markdown_blocks

    return parse_markdown_blocks(content)


def _create_chat_session(*, system: str = "", max_history: int | None = None):
    from chattool.tools.lark.session import ChatSession

    return ChatSession(system=system, max_history=max_history)


def _require_dict_payload(path: str, label: str) -> dict:
    payload = _load_json_file(path)
    if not isinstance(payload, dict):
        raise click.ClickException(f"{label} JSON 顶层必须是对象")
    return payload


def _require_list_payload(path: str, label: str) -> list:
    payload = _load_json_file(path)
    if not isinstance(payload, list):
        raise click.ClickException(f"{label} JSON 顶层必须是数组")
    return payload


def _parse_iso_datetime(value: str, label: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise click.ClickException(
            f"{label} 时间格式无效: {value}。请使用 ISO8601，例如 2026-03-24T14:00:00+08:00"
        ) from exc
    if dt.tzinfo is None:
        raise click.ClickException(
            f"{label} 必须包含时区信息，例如 2026-03-24T14:00:00+08:00"
        )
    return dt


def _iso_to_unix_seconds(value: str, label: str) -> int:
    return int(_parse_iso_datetime(value, label).timestamp())


def _iso_to_time_info(value: str, label: str) -> dict[str, str]:
    dt = _parse_iso_datetime(value, label)
    tz_name = dt.tzname() or "UTC"
    return {
        "timestamp": str(int(dt.timestamp())),
        "timezone": tz_name,
    }


def _extract_json_path(payload: dict, *path: str):
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _pick_calendar_id_from_payload(payload: dict) -> str | None:
    direct = (
        _extract_json_path(payload, "data", "calendar", "calendar_id")
        or _extract_json_path(payload, "data", "primary_calendar", "calendar_id")
        or _extract_json_path(payload, "data", "calendar_id")
    )
    if direct:
        return direct

    calendar_list = _extract_json_path(payload, "data", "calendar_list") or []
    if isinstance(calendar_list, list):
        for item in calendar_list:
            if isinstance(item, dict) and item.get("type") == "primary" and item.get("calendar_id"):
                return item["calendar_id"]
        for item in calendar_list:
            if isinstance(item, dict) and item.get("calendar_id"):
                return item["calendar_id"]
    return None


def _resolve_calendar_id(bot, calendar_id: str | None, user_id_type: str) -> str:
    if calendar_id:
        return calendar_id

    resp = bot.get_primary_calendar(user_id_type=user_id_type)
    payload = _response_json(resp)
    resolved = _pick_calendar_id_from_payload(payload) if resp.success() else None
    if resolved:
        return resolved

    fallback_resp = bot.list_calendars()
    if _print_lark_error("列出可用日历", fallback_resp):
        raise click.Abort()

    fallback_payload = _response_json(fallback_resp)
    resolved = _pick_calendar_id_from_payload(fallback_payload)
    if not resolved:
        raise click.ClickException("未能从返回结果中解析默认 calendar_id")
    return resolved


def _get_test_user_member() -> dict | None:
    user_id = FeishuConfig.FEISHU_TEST_USER_ID.value or None
    if not user_id:
        return None
    return {
        "id": user_id,
        "type": FeishuConfig.FEISHU_TEST_USER_ID_TYPE.value or "user_id",
        "role": "assignee",
    }


def _print_topic_result(title: str, payload: dict) -> None:
    click.secho(f"✅ {title}", fg="green")
    _print_json(payload)


def _get_permission_notice_target() -> tuple[str | None, str]:
    test_user_id = FeishuConfig.FEISHU_TEST_USER_ID.value or None
    if test_user_id:
        return test_user_id, FeishuConfig.FEISHU_TEST_USER_ID_TYPE.value or "user_id"

    default_receiver = FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value or None
    if default_receiver:
        return default_receiver, "user_id"

    return None, "user_id"


def _granted_scope_names(resp) -> list[str]:
    scopes = getattr(getattr(resp, "data", None), "scopes", None) or []
    names = []
    for scope in scopes:
        if getattr(scope, "grant_status", None) == 1 and getattr(scope, "scope_name", None):
            names.append(scope.scope_name)
    return names


def _scope_category_status(granted_scopes: list[str]) -> dict[str, list[str]]:
    rules = {
        "im": ["im:"],
        "docx/drive": ["docx:", "drive:"],
        "bitable": ["bitable:"],
        "calendar": ["calendar:"],
        "task": ["task:"],
    }
    return {
        name: [scope for scope in granted_scopes if any(pattern in scope for pattern in patterns)]
        for name, patterns in rules.items()
    }


def _print_scope_category_summary(granted_scopes: list[str], *, title: str = "关键能力分类") -> list[str]:
    categories = _scope_category_status(granted_scopes)
    missing = [name for name, matches in categories.items() if not matches]
    click.secho(f"\n{title}", fg="cyan", bold=True)
    for name, matches in categories.items():
        click.echo(f"  {name:10}: {'ok' if matches else 'missing'} ({len(matches)})")
    if missing:
        click.secho(
            "  可能存在权限问题，缺失分类: " + ", ".join(missing),
            fg="yellow",
        )
        click.echo("  建议先执行 `chattool lark troubleshoot check-scopes` 做进一步确认。")
    return missing


def _build_scope_check_card(
    categories: dict[str, list[str]],
    missing: list[str],
    *,
    failed_command: str | None = None,
    failed_code: int | None = None,
    failed_msg: str | None = None,
) -> dict:
    lines = []
    for name, matches in categories.items():
        status = "missing" if not matches else f"ok ({len(matches)})"
        lines.append(f"- `{name}`: {status}")

    app_id = FeishuConfig.FEISHU_APP_ID.value or ""
    app_line = f"当前 App ID: `{app_id}`" if app_id else "当前 App ID 未配置，请先检查 `FEISHU_APP_ID`。"
    platform_url = "https://open.feishu.cn/app"
    permission_doc_url = "https://open.feishu.cn/document/server-docs/application-v6/app-permission/list"

    if missing:
        summary = "检测到关键权限分类缺失，相关 CLI 能力可能会因 scope 不足失败。"
        template = "orange"
        advice = [
            "1. 点击下方按钮打开飞书开放平台应用页。",
            "2. 在权限管理中申请并开通缺失分类对应的 scopes。",
            "3. 发布配置后重新执行 `chattool lark troubleshoot check-scopes`。",
        ]
    else:
        summary = "关键权限分类均已命中，若仍失败，优先继续排查接收者范围、事件配置或业务参数。"
        template = "green"
        advice = [
            "1. 如消息仍失败，可点击按钮进入开放平台继续核对应用配置。",
            "2. 然后执行 `chattool lark troubleshoot doctor` 检查接收者范围、事件订阅和卡片回传配置。",
        ]

    context_lines = []
    if failed_command:
        context_lines.append(f"失败命令: `{failed_command}`")
    if failed_code is not None:
        context_lines.append(f"错误码: `{failed_code}`")
    if failed_msg:
        context_lines.append(f"错误信息: `{failed_msg}`")

    elements = []
    if context_lines:
        elements.append({"tag": "markdown", "content": "\n".join(context_lines)})
        elements.append({"tag": "hr"})

    elements.extend(
        [
            {"tag": "markdown", "content": summary},
            {"tag": "markdown", "content": "\n".join(lines)},
            {"tag": "markdown", "content": app_line},
            {"tag": "hr"},
            {"tag": "markdown", "content": "\n".join(advice)},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "打开开放平台"},
                        "type": "primary",
                        "url": platform_url,
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看权限文档"},
                        "type": "default",
                        "url": permission_doc_url,
                    },
                ],
            },
        ]
    )

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "ChatTool Feishu Scope Check"},
            "template": template,
        },
        "elements": elements,
    }


def _handle_permission_denied(bot, resp, *, failed_command: str) -> None:
    click.echo("  → 提示: 权限不足，开始执行 scope 诊断")

    scopes_resp = bot.get_scopes()
    if not scopes_resp.success():
        click.echo(
            "  → scopes 诊断失败，"
            f"code={scopes_resp.code} msg={scopes_resp.msg}"
        )
        return

    granted = _granted_scope_names(scopes_resp)
    categories = _scope_category_status(granted)
    missing = [name for name, matches in categories.items() if not matches]
    _print_scope_category_summary(granted, title="权限诊断")

    card = _build_scope_check_card(
        categories,
        missing,
        failed_command=failed_command,
        failed_code=getattr(resp, "code", None),
        failed_msg=getattr(resp, "msg", None),
    )
    card_path = Path("/tmp/chattool-lark-permission-card.json")
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    click.echo(f"  → 权限引导卡已导出: {card_path}")

    target, target_type = _get_permission_notice_target()
    if not target:
        click.echo("  → 未配置 FEISHU_TEST_USER_ID 或 FEISHU_DEFAULT_RECEIVER_ID，跳过自动发卡")
        return

    send_resp = bot.send_card(target, target_type, card)
    if send_resp.success():
        click.echo(
            "  → 权限引导卡已发送: "
            f"{target_type}={target}  message_id={send_resp.data.message_id}"
        )
        return

    click.echo(
        "  → 自动发送权限引导卡失败: "
        f"code={send_resp.code} msg={send_resp.msg}"
    )


# ------------------------------------------------------------------
# chattool lark info
# ------------------------------------------------------------------

@cli.command()
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def info(env_ref):
    """获取机器人基本信息（验证凭证）"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_bot_info()

    if resp.code != 0:
        click.secho(f"请求失败: code={resp.code}", fg="red")
        return

    data = json.loads(resp.raw.content).get("bot", {})
    status_map = {1: "未激活", 2: "已激活", 3: "已停用"}
    status = status_map.get(data.get("activate_status"), "未知")
    click.echo(f"名称      : {data.get('app_name', '—')}")
    click.echo(f"Open ID   : {data.get('open_id', '—')}")
    click.echo(f"激活状态  : {status}")


# ------------------------------------------------------------------
# chattool lark scopes
# ------------------------------------------------------------------

@cli.command()
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--all", "-a", "show_all", is_flag=True,
              help="显示全部权限（包括未授权的）")
@click.option("--filter", "-f", "keyword", default=None,
              help="按关键字过滤 (如 im, calendar, drive)")
@click.option("--group", "-g", is_flag=True,
              help="按模块分组显示")
def scopes(env_ref, show_all, keyword, group):
    """查看应用已申请的权限列表"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_scopes()

    if not resp.success():
        click.secho(f"请求失败: code={resp.code}  msg={resp.msg}", fg="red")
        return

    all_scopes = resp.data.scopes or []
    if not all_scopes:
        click.echo("未找到任何权限记录")
        return

    granted_scopes = _granted_scope_names(resp)
    scope_list = list(all_scopes)

    if not show_all:
        scope_list = [s for s in scope_list if s.grant_status == 1]

    if keyword:
        kw = keyword.lower()
        scope_list = [s for s in scope_list if kw in (s.scope_name or "").lower()]

    if not scope_list:
        if keyword:
            matching_all = [
                s for s in all_scopes
                if keyword.lower() in (s.scope_name or "").lower()
            ]
            if matching_all:
                click.secho("没有匹配的已授权权限", fg="yellow")
                click.echo("检测到同名权限记录，但当前 grant_status 不是已授权：")
                status_label = {0: "未授权", 1: "已授权", 2: "已过期"}
                for s in sorted(matching_all, key=lambda x: x.scope_name or ""):
                    click.echo(f"  {s.scope_name}  [{status_label.get(s.grant_status, '?')}]")
                click.echo("这通常意味着相关能力会因权限不足而失败。")
                _print_scope_category_summary(granted_scopes, title="关键能力分类")
                return
        click.echo("没有匹配的权限")
        return

    status_label = {0: "未授权", 1: "已授权", 2: "已过期"}
    status_color = {0: "yellow", 1: "green", 2: "red"}

    sorted_scopes = sorted(scope_list, key=lambda x: x.scope_name or "")

    if group:
        groups = defaultdict(list)
        for s in sorted_scopes:
            prefix = (s.scope_name or "unknown").split(":")[0]
            groups[prefix].append(s)

        for prefix in sorted(groups):
            items = groups[prefix]
            granted_count = sum(1 for s in items if s.grant_status == 1)
            click.secho(f"\n{prefix} ({granted_count}/{len(items)})", fg="cyan", bold=True)
            for s in items:
                name_rest = s.scope_name[len(prefix)+1:] if ":" in s.scope_name else s.scope_name
                if show_all and s.grant_status != 1:
                    label = status_label.get(s.grant_status, "?")
                    color = status_color.get(s.grant_status, "white")
                    click.secho(f"  {name_rest}  [{label}]", fg=color)
                else:
                    click.echo(f"  {name_rest}")
    else:
        label = "全部" if show_all else "已授权"
        click.secho(f"{label} ({len(sorted_scopes)}):", bold=True)
        for s in sorted_scopes:
            if show_all and s.grant_status != 1:
                label_s = status_label.get(s.grant_status, "?")
                color = status_color.get(s.grant_status, "white")
                click.secho(f"  {s.scope_name}  [{label_s}]", fg=color)
            else:
                click.echo(f"  {s.scope_name}")

    _print_scope_category_summary(granted_scopes)


# ------------------------------------------------------------------
# chattool lark send
# ------------------------------------------------------------------

@cli.command()
@click.argument("receiver", required=False)
@click.argument("text", required=False, default="")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--type", "-t", "id_type",
              default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id", "email", "chat_id"]),
              help="接收者 ID 类型 (默认 user_id)")
@click.option("--image", "-i", "image_path",
              type=click.Path(exists=True),
              help="发送图片（本地文件路径）")
@click.option("--file", "file_path",
              type=click.Path(exists=True),
              help="发送文件（本地文件路径）")
@click.option("--card", "-c", "card_file",
              type=click.Path(exists=True),
              help="发送卡片消息（JSON 文件路径）")
@click.option("--post", "-p", "post_file",
              type=click.Path(exists=True),
              help="发送富文本消息（JSON 文件路径）")
def send(receiver, text, env_ref, id_type, image_path, file_path, card_file, post_file):
    """
    发送消息给指定用户或群。

    \b
    示例:
      chattool lark send "你好，世界"
      chattool lark send rexwzh "你好，世界"
      chattool lark send rexwzh "你好，世界" -e work
      chattool lark send rexwzh --image photo.jpg
      chattool lark send rexwzh --file report.pdf
      chattool lark send rexwzh --card card.json
      chattool lark send oc_xxx "群消息" -t chat_id
    """
    _load_runtime_env(env_ref)
    bot = _get_bot()
    receiver, text = _resolve_receiver_and_text(
        receiver,
        text,
        has_structured_content=bool(image_path or file_path or card_file or post_file),
    )

    if receiver and not text and not (image_path or file_path or card_file or post_file) and not _has_default_receiver():
        click.secho(
            "单参数形式需要先配置 FEISHU_DEFAULT_RECEIVER_ID；"
            "否则请显式传入 receiver 和 text",
            fg="red",
        )
        return

    if not receiver:
        click.secho(
            "请指定接收者，或先配置 FEISHU_DEFAULT_RECEIVER_ID 作为默认发送目标",
            fg="red",
        )
        return

    if image_path:
        resp = bot.send_image_file(receiver, id_type, image_path)
        msg_type = "图片"
    elif file_path:
        resp = bot.send_file(receiver, id_type, file_path)
        msg_type = "文件"
    elif card_file:
        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)
        resp = bot.send_card(receiver, id_type, card)
        msg_type = "卡片"
    elif post_file:
        with open(post_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        resp = bot.send_post(receiver, id_type, content)
        msg_type = "富文本"
    elif text:
        resp = bot.send_text(receiver, id_type, text)
        msg_type = "文本"
    else:
        click.secho("请指定消息内容: TEXT、--image、--file、--card 或 --post", fg="red")
        return

    if resp.success():
        click.secho(
            f"✅ {msg_type}消息发送成功  message_id={resp.data.message_id}",
            fg="green",
        )
    else:
        click.secho(f"❌ 发送失败: code={resp.code}  msg={resp.msg}", fg="red")
        if resp.code in (99991672, 230013):
            _handle_permission_denied(
                bot,
                resp,
                failed_command=f"chattool lark send ({msg_type})",
            )
        elif resp.code == 99991663:
            click.echo("  → 提示: 用户不在应用可见范围内")


@cli.command("notify-doc")
@click.argument("title")
@click.argument("text", required=False, default="")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--receiver", "-r", default=None,
              help="通知接收者，默认使用 FEISHU_DEFAULT_RECEIVER_ID")
@click.option("--type", "-t", "id_type",
              default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id", "email", "chat_id"]),
              help="接收者 ID 类型 (默认 user_id)")
@click.option("--folder-token", default=None,
              help="可选：父文件夹 token")
@click.option("--append-file", type=click.Path(exists=True, dir_okay=False),
              default=None, help="从本地 txt/md 文件追加正文")
@click.option("--batch-size", type=int, default=20, show_default=True,
              help="每次向飞书文档追加的段落数，失败时会自动回退到单段写入")
@click.option("--open/--no-open", "open_after", default=False,
              help="成功后在本地打开文档链接")
def notify_doc(title, text, env_ref, receiver, id_type, folder_token, append_file, batch_size, open_after):
    """创建文档并把链接发送给目标用户"""
    _load_runtime_env(env_ref)
    receiver = _resolve_message_receiver(receiver)
    if not receiver:
        click.secho(
            "请通过 --receiver 指定接收者，或先配置 FEISHU_DEFAULT_RECEIVER_ID",
            fg="red",
        )
        return

    bot = _get_bot()
    create_resp = bot.create_doc_document(title, folder_token=folder_token)
    if _print_lark_error("创建文档", create_resp):
        return

    document = create_resp.data.document
    paragraphs = []
    if text:
        paragraphs.append(text)
    paragraphs.extend(_read_append_file_paragraphs(append_file))

    if paragraphs:
        append_resp = _append_doc_paragraphs(
            bot,
            document.document_id,
            paragraphs,
            batch_size=batch_size,
        )
        if _print_lark_error("追加文档文本", append_resp):
            return
        document.revision_id = getattr(append_resp.data, "document_revision_id", document.revision_id)

    meta_resp = bot.get_doc_meta(document.document_id, with_url=True)
    if _print_lark_error("获取文档链接", meta_resp):
        return

    metas = getattr(meta_resp.data, "metas", None) or []
    doc_url = metas[0].url if metas else None
    if not doc_url:
        click.secho("❌ 获取文档链接失败: 返回结果中没有 url", fg="red")
        return

    message_lines = [f"📄 {document.title}", doc_url]
    if paragraphs:
        message_lines.insert(1, "")
        preview = paragraphs[0]
        if len(paragraphs) > 1:
            preview += f"\n... (+{len(paragraphs) - 1} 段)"
        message_lines.insert(2, preview)
    notify_resp = bot.send_text(receiver, id_type, "\n".join(message_lines))
    if _print_lark_error("发送文档通知", notify_resp):
        return

    click.secho(
        f"✅ 文档通知发送成功  message_id={notify_resp.data.message_id}",
        fg="green",
    )
    click.echo(f"document_id: {document.document_id}")
    click.echo(f"url        : {doc_url}")
    if open_after:
        try:
            click.launch(doc_url)
        except Exception as e:
            click.secho(f"⚠️ 打开文档失败: {e}", fg="yellow")

# ------------------------------------------------------------------
# chattool lark upload
# ------------------------------------------------------------------

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--type", "-t", "upload_type", default="auto",
              type=click.Choice(["auto", "image", "file"]),
              help="上传类型 (默认 auto，根据扩展名判断)")
def upload(path, env_ref, upload_type):
    """
    上传图片或文件到飞书，返回 image_key / file_key。

    \b
    示例:
      chattool lark upload photo.jpg
      chattool lark upload report.pdf
      chattool lark upload data.bin -t file
    """
    _load_runtime_env(env_ref)
    bot = _get_bot()

    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".tiff"}
    ext = os.path.splitext(path)[1].lower()

    if upload_type == "auto":
        is_image = ext in image_exts
    else:
        is_image = upload_type == "image"

    if is_image:
        resp = bot.upload_image(path)
        if resp.success():
            click.secho(f"✅ 上传成功  image_key={resp.data.image_key}", fg="green")
        else:
            click.secho(f"❌ 上传失败: code={resp.code}  msg={resp.msg}", fg="red")
    else:
        resp = bot.upload_file(path)
        if resp.success():
            click.secho(f"✅ 上传成功  file_key={resp.data.file_key}", fg="green")
        else:
            click.secho(f"❌ 上传失败: code={resp.code}  msg={resp.msg}", fg="red")


# ------------------------------------------------------------------
# chattool lark reply
# ------------------------------------------------------------------

@cli.command()
@click.argument("message_id")
@click.argument("text")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def reply(message_id, text, env_ref):
    """
    引用回复一条消息。

    \b
    示例:
      chattool lark reply om_xxx "收到，已处理"
    """
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.reply(message_id, text)
    if resp.success():
        click.secho(f"✅ 回复成功  message_id={resp.data.message_id}", fg="green")
    else:
        click.secho(f"❌ 回复失败: code={resp.code}  msg={resp.msg}", fg="red")


# ------------------------------------------------------------------
# chattool lark doc
# ------------------------------------------------------------------

@cli.group()
def doc():
    """飞书云文档工具"""
    pass


@doc.command("create")
@click.argument("title")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--folder-token", default=None,
              help="可选：父文件夹 token")
def doc_create(title, env_ref, folder_token):
    """创建云文档"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.create_doc_document(title, folder_token=folder_token)
    if _print_lark_error("创建文档", resp):
        return

    document = resp.data.document
    click.secho(f"✅ 文档创建成功  document_id={document.document_id}", fg="green")
    click.echo(f"标题      : {document.title}")
    click.echo(f"revision  : {document.revision_id}")


@doc.command("get")
@click.argument("document_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def doc_get(document_id, env_ref):
    """获取文档元信息"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_doc_document(document_id)
    if _print_lark_error("获取文档", resp):
        return

    document = resp.data.document
    click.echo(f"document_id: {document.document_id}")
    click.echo(f"标题       : {document.title}")
    click.echo(f"revision   : {document.revision_id}")


@doc.command("raw")
@click.argument("document_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--lang", type=int, default=None,
              help="可选：语言参数，透传到 raw_content 接口")
def doc_raw(document_id, env_ref, lang):
    """获取文档纯文本内容"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_doc_raw_content(document_id, lang=lang)
    if _print_lark_error("获取文档纯文本", resp):
        return

    click.echo(resp.data.content or "")


@doc.command("blocks")
@click.argument("document_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--block-id", default=None,
              help="父 block_id，默认使用 document_id")
@click.option("--page-size", type=int, default=20,
              help="每页数量 (默认 20)")
@click.option("--page-token", default=None,
              help="分页 token")
@click.option("--descendants/--no-descendants", default=False,
              help="是否递归展开后代块")
def doc_blocks(document_id, env_ref, block_id, page_size, page_token, descendants):
    """列出文档块"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_doc_block_children(
        document_id=document_id,
        block_id=block_id or document_id,
        page_size=page_size,
        page_token=page_token,
        with_descendants=descendants,
    )
    if _print_lark_error("获取文档块", resp):
        return

    items = resp.data.items or []
    click.secho(
        f"✅ 获取成功  items={len(items)}  has_more={bool(resp.data.has_more)}",
        fg="green",
    )
    for item in items:
        child_count = len(item.children or [])
        click.echo(
            f"- block_id={item.block_id}  type={item.block_type}  children={child_count}"
        )
    if resp.data.page_token:
        click.echo(f"next_page_token: {resp.data.page_token}")


@doc.command("append-text")
@click.argument("document_id")
@click.argument("text")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--block-id", default=None,
              help="父 block_id，默认使用 document_id")
@click.option("--index", type=int, default=None,
              help="插入位置，留空则交由服务端处理")
def doc_append_text(document_id, text, env_ref, block_id, index):
    """向文档追加一段纯文本"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.append_doc_text(
        document_id=document_id,
        text=text,
        block_id=block_id,
        index=index,
    )
    if _print_lark_error("追加文档文本", resp):
        return

    revision_id = getattr(resp.data, "document_revision_id", None)
    click.secho("✅ 追加成功", fg="green")
    if revision_id is not None:
        click.echo(f"revision  : {revision_id}")
    children = getattr(resp.data, "children", None) or []
    click.echo(f"children   : {len(children)}")


@doc.command("append-file")
@click.argument("document_id")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--block-id", default=None,
              help="父 block_id，默认使用 document_id")
@click.option("--index", type=int, default=None,
              help="插入位置，留空则交由服务端处理")
@click.option("--batch-size", type=int, default=20, show_default=True,
              help="每次向飞书文档追加的段落数，失败时会自动回退到单段写入")
def doc_append_file(document_id, path, env_ref, block_id, index, batch_size):
    """向文档追加本地 txt/md 文件内容"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    paragraphs = _read_append_file_paragraphs(path)
    if not paragraphs:
        click.secho("文件中没有可追加的正文段落", fg="yellow")
        return

    resp = _append_doc_paragraphs(
        bot,
        document_id=document_id,
        paragraphs=paragraphs,
        block_id=block_id,
        index=index,
        batch_size=batch_size,
    )
    if _print_lark_error("追加文档文件", resp):
        return

    revision_id = getattr(resp.data, "document_revision_id", None)
    click.secho("✅ 文件追加成功", fg="green")
    click.echo(f"paragraphs : {len(paragraphs)}")
    if revision_id is not None:
        click.echo(f"revision   : {revision_id}")
    children = getattr(resp.data, "children", None) or []
    click.echo(f"children   : {len(children)}")


@doc.command("parse-md")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", type=click.Path(dir_okay=False), default=None,
              help="输出 JSON 文件路径，默认打印到标准输出")
@click.option("--compact/--pretty", default=False,
              help="输出紧凑 JSON，默认使用 pretty 格式")
def doc_parse_md(path, output, compact):
    """将 Markdown 转换为飞书 docx block JSON"""
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    blocks = _parse_markdown_blocks(content)
    payload = json.dumps(
        blocks,
        ensure_ascii=False,
        separators=(",", ":") if compact else None,
        indent=None if compact else 2,
    )

    if output:
        Path(output).write_text(payload + ("\n" if not compact else ""), encoding="utf-8")
        click.secho(f"✅ 已写入 {output}", fg="green")
        click.echo(f"blocks     : {len(blocks)}")
        return

    click.echo(payload)


@doc.command("append-json")
@click.argument("document_id")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--block-id", default=None,
              help="父 block_id，默认使用 document_id")
@click.option("--index", type=int, default=None,
              help="插入位置，留空则交由服务端处理")
@click.option("--batch-size", type=int, default=20, show_default=True,
              help="每次向飞书文档追加的 block 数")
def doc_append_json(document_id, path, env_ref, block_id, index, batch_size):
    """将 block JSON 追加到飞书文档"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise click.ClickException("JSON 顶层必须是 block 数组")

    resp = bot.append_doc_blocks_safe(
        document_id=document_id,
        blocks=payload,
        block_id=block_id,
        index=index,
        batch_size=batch_size,
    )
    if _print_lark_error("追加文档 JSON", resp):
        return

    revision_id = getattr(resp.data, "document_revision_id", None)
    click.secho("✅ JSON 追加成功", fg="green")
    click.echo(f"blocks     : {len(payload)}")
    if revision_id is not None:
        click.echo(f"revision   : {revision_id}")
    children = getattr(resp.data, "children", None) or []
    click.echo(f"children   : {len(children)}")


# ------------------------------------------------------------------
# chattool lark bitable
# ------------------------------------------------------------------

@cli.group()
def bitable():
    """飞书多维表格工具"""
    pass


@bitable.group()
def app():
    """Bitable app 相关命令"""
    pass


@app.command("create")
@click.argument("name")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--folder-token", default=None, help="可选：父文件夹 token")
@click.option("--time-zone", default=None, help="可选：表格时区，例如 Asia/Shanghai")
def bitable_app_create(name, env_ref, folder_token, time_zone):
    """创建 Bitable app"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.create_bitable_app(name, folder_token=folder_token, time_zone=time_zone)
    if _print_lark_error("创建 Bitable app", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("Bitable app 创建成功", payload)


@bitable.group()
def table():
    """Bitable table 相关命令"""
    pass


@table.command("list")
@click.argument("app_token")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--page-size", type=int, default=100, show_default=True)
@click.option("--page-token", default=None)
def bitable_table_list(app_token, env_ref, page_size, page_token):
    """列出 Bitable app 下的数据表"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_bitable_tables(app_token, page_size=page_size, page_token=page_token)
    if _print_lark_error("列出数据表", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("数据表列表获取成功", payload)


@table.command("create")
@click.argument("app_token")
@click.argument("name")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--default-view-name", default=None, help="默认视图名称")
@click.option("--fields-json", type=click.Path(exists=True, dir_okay=False), default=None,
              help="可选：初始字段数组 JSON")
def bitable_table_create(app_token, name, env_ref, default_view_name, fields_json):
    """创建数据表"""
    _load_runtime_env(env_ref)
    fields = None
    if fields_json:
        fields = _require_list_payload(fields_json, "fields")
    bot = _get_bot()
    resp = bot.create_bitable_table(
        app_token,
        name,
        default_view_name=default_view_name,
        fields=fields,
    )
    if _print_lark_error("创建数据表", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("数据表创建成功", payload)


@bitable.group()
def field():
    """Bitable field 相关命令"""
    pass


@field.command("list")
@click.argument("app_token")
@click.argument("table_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--page-size", type=int, default=100, show_default=True)
@click.option("--page-token", default=None)
def bitable_field_list(app_token, table_id, env_ref, page_size, page_token):
    """列出字段"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_bitable_fields(
        app_token,
        table_id,
        page_size=page_size,
        page_token=page_token,
    )
    if _print_lark_error("列出字段", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("字段列表获取成功", payload)


@field.command("create")
@click.argument("app_token")
@click.argument("table_id")
@click.argument("field_name")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--type", "field_type", type=int, required=True, help="飞书字段类型整数值")
@click.option("--property-json", type=click.Path(exists=True, dir_okay=False), default=None,
              help="可选：字段 property JSON")
@click.option("--description-json", type=click.Path(exists=True, dir_okay=False), default=None,
              help="可选：字段 description JSON")
@click.option("--ui-type", default=None, help="可选：字段 UI 类型")
@click.option("--primary", is_flag=True, help="设为主字段")
@click.option("--hidden", is_flag=True, help="设为隐藏字段")
def bitable_field_create(
    app_token,
    table_id,
    field_name,
    env_ref,
    field_type,
    property_json,
    description_json,
    ui_type,
    primary,
    hidden,
):
    """创建字段"""
    _load_runtime_env(env_ref)
    property_payload = _require_dict_payload(property_json, "property") if property_json else None
    description_payload = _require_dict_payload(description_json, "description") if description_json else None
    bot = _get_bot()
    resp = bot.create_bitable_field(
        app_token,
        table_id,
        field_name,
        field_type,
        property=property_payload,
        description=description_payload,
        ui_type=ui_type,
        is_primary=True if primary else None,
        is_hidden=True if hidden else None,
    )
    if _print_lark_error("创建字段", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("字段创建成功", payload)


@bitable.group()
def record():
    """Bitable record 相关命令"""
    pass


@record.command("list")
@click.argument("app_token")
@click.argument("table_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
@click.option("--page-size", type=int, default=100, show_default=True)
@click.option("--page-token", default=None)
def bitable_record_list(app_token, table_id, env_ref, user_id_type, page_size, page_token):
    """列出记录"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_bitable_records(
        app_token,
        table_id,
        page_size=page_size,
        page_token=page_token,
        user_id_type=user_id_type,
    )
    if _print_lark_error("列出记录", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("记录列表获取成功", payload)


@record.command("create")
@click.argument("app_token")
@click.argument("table_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--json", "json_path", type=click.Path(exists=True, dir_okay=False), required=True,
              help="记录字段 JSON")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def bitable_record_create(app_token, table_id, env_ref, json_path, user_id_type):
    """创建一条记录"""
    _load_runtime_env(env_ref)
    fields = _require_dict_payload(json_path, "record")
    bot = _get_bot()
    resp = bot.create_bitable_record(
        app_token,
        table_id,
        fields=fields,
        user_id_type=user_id_type,
    )
    if _print_lark_error("创建记录", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("记录创建成功", payload)


@record.command("batch-create")
@click.argument("app_token")
@click.argument("table_id")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--json", "json_path", type=click.Path(exists=True, dir_okay=False), required=True,
              help="记录数组 JSON，每一项是 fields 对象")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def bitable_record_batch_create(app_token, table_id, env_ref, json_path, user_id_type):
    """批量创建记录"""
    _load_runtime_env(env_ref)
    records_payload = _require_list_payload(json_path, "records")
    if not all(isinstance(item, dict) for item in records_payload):
        raise click.ClickException("records JSON 必须是对象数组")
    bot = _get_bot()
    resp = bot.batch_create_bitable_records(
        app_token,
        table_id,
        records=records_payload,
        user_id_type=user_id_type,
    )
    if _print_lark_error("批量创建记录", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("记录批量创建成功", payload)


# ------------------------------------------------------------------
# chattool lark calendar
# ------------------------------------------------------------------

@cli.group()
def calendar():
    """飞书日历工具"""
    pass


@calendar.command("primary")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_primary(env_ref, user_id_type):
    """查看默认日历"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    try:
        resolved_calendar_id = _resolve_calendar_id(bot, None, user_id_type)
    except click.Abort:
        return
    payload = _response_json(bot.list_calendars())
    payload["resolved_calendar_id"] = resolved_calendar_id
    _print_topic_result("默认日历获取成功", payload)


@calendar.group()
def event():
    """Calendar event 相关命令"""
    pass


@event.command("create")
@click.option("--summary", required=True, help="日程标题")
@click.option("--start", "start_value", required=True,
              help="开始时间，ISO8601，例如 2026-03-24T14:00:00+08:00")
@click.option("--end", "end_value", required=True,
              help="结束时间，ISO8601，例如 2026-03-24T15:00:00+08:00")
@click.option("--description", default=None, help="可选：日程描述")
@click.option("--calendar-id", default=None, help="可选：日历 ID，默认自动取 primary")
@click.option("--need-notification/--no-need-notification", default=None,
              help="可选：是否触发通知")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_event_create(
    summary,
    start_value,
    end_value,
    description,
    calendar_id,
    need_notification,
    env_ref,
    user_id_type,
):
    """创建日程"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resolved_calendar_id = _resolve_calendar_id(bot, calendar_id, user_id_type)
    resp = bot.create_calendar_event(
        resolved_calendar_id,
        summary=summary,
        start_time=_iso_to_time_info(start_value, "start"),
        end_time=_iso_to_time_info(end_value, "end"),
        description=description,
        need_notification=need_notification,
        user_id_type=user_id_type,
    )
    if _print_lark_error("创建日程", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("日程创建成功", payload)


@event.command("list")
@click.option("--start", "start_value", required=True,
              help="开始时间，ISO8601")
@click.option("--end", "end_value", required=True,
              help="结束时间，ISO8601")
@click.option("--calendar-id", default=None, help="可选：日历 ID，默认自动取 primary")
@click.option("--page-size", type=int, default=50, show_default=True)
@click.option("--page-token", default=None)
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_event_list(start_value, end_value, calendar_id, page_size, page_token, env_ref, user_id_type):
    """列出时间范围内的日程"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resolved_calendar_id = _resolve_calendar_id(bot, calendar_id, user_id_type)
    resp = bot.list_calendar_events(
        resolved_calendar_id,
        start_time=str(_iso_to_unix_seconds(start_value, "start")),
        end_time=str(_iso_to_unix_seconds(end_value, "end")),
        page_size=page_size,
        page_token=page_token,
        user_id_type=user_id_type,
    )
    if _print_lark_error("列出日程", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("日程列表获取成功", payload)


@event.command("get")
@click.argument("event_id")
@click.option("--calendar-id", default=None, help="可选：日历 ID，默认自动取 primary")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_event_get(event_id, calendar_id, env_ref, user_id_type):
    """获取单个日程"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resolved_calendar_id = _resolve_calendar_id(bot, calendar_id, user_id_type)
    resp = bot.get_calendar_event(
        resolved_calendar_id,
        event_id=event_id,
        user_id_type=user_id_type,
    )
    if _print_lark_error("获取日程", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("日程获取成功", payload)


@event.command("patch")
@click.argument("event_id")
@click.option("--summary", default=None, help="可选：新标题")
@click.option("--start", "start_value", default=None, help="可选：新开始时间，ISO8601")
@click.option("--end", "end_value", default=None, help="可选：新结束时间，ISO8601")
@click.option("--description", default=None, help="可选：新描述")
@click.option("--calendar-id", default=None, help="可选：日历 ID，默认自动取 primary")
@click.option("--need-notification/--no-need-notification", default=None,
              help="可选：是否触发通知")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_event_patch(
    event_id,
    summary,
    start_value,
    end_value,
    description,
    calendar_id,
    need_notification,
    env_ref,
    user_id_type,
):
    """更新日程"""
    if not any([summary, start_value, end_value, description, need_notification is not None]):
        raise click.ClickException("请至少提供一个更新项，如 --summary / --start / --end / --description")

    _load_runtime_env(env_ref)
    bot = _get_bot()
    resolved_calendar_id = _resolve_calendar_id(bot, calendar_id, user_id_type)
    resp = bot.patch_calendar_event(
        resolved_calendar_id,
        event_id=event_id,
        summary=summary,
        start_time=_iso_to_time_info(start_value, "start") if start_value else None,
        end_time=_iso_to_time_info(end_value, "end") if end_value else None,
        description=description,
        need_notification=need_notification,
        user_id_type=user_id_type,
    )
    if _print_lark_error("更新日程", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("日程更新成功", payload)


@event.command("reply")
@click.argument("event_id")
@click.option("--status", required=True,
              type=click.Choice(["accept", "decline", "tentative"], case_sensitive=False))
@click.option("--calendar-id", default=None, help="可选：日历 ID，默认自动取 primary")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_event_reply(event_id, status, calendar_id, env_ref, user_id_type):
    """回复日程邀请"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resolved_calendar_id = _resolve_calendar_id(bot, calendar_id, user_id_type)
    resp = bot.reply_calendar_event(
        resolved_calendar_id,
        event_id=event_id,
        rsvp_status=status.lower(),
    )
    if _print_lark_error("回复日程邀请", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("日程邀请回复成功", payload)


@calendar.group()
def freebusy():
    """freebusy 相关命令"""
    pass


@freebusy.command("list")
@click.option("--start", "start_value", required=True, help="开始时间，ISO8601")
@click.option("--end", "end_value", required=True, help="结束时间，ISO8601")
@click.option("--json", "json_path", type=click.Path(exists=True, dir_okay=False), default=None,
              help="用户/会议室 JSON。可传数组，或 {\"user_ids\": [...], \"room_ids\": [...]} 对象")
@click.option("--include-external-calendar", is_flag=True, help="包含外部日历")
@click.option("--only-busy", is_flag=True, help="仅返回 busy 段")
@click.option("--need-rsvp-status", is_flag=True, help="返回 RSVP 状态")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def calendar_freebusy_list(
    start_value,
    end_value,
    json_path,
    include_external_calendar,
    only_busy,
    need_rsvp_status,
    env_ref,
    user_id_type,
):
    """查询忙闲"""
    _load_runtime_env(env_ref)

    user_ids = None
    room_ids = None
    if json_path:
        payload = _load_json_file(json_path)
        if isinstance(payload, list):
            user_ids = payload
        elif isinstance(payload, dict):
            user_ids = payload.get("user_ids")
            room_ids = payload.get("room_ids")
        else:
            raise click.ClickException("freebusy JSON 必须是数组或对象")
    else:
        test_user = FeishuConfig.FEISHU_TEST_USER_ID.value or None
        if test_user:
            user_ids = [test_user]
        else:
            raise click.ClickException("请通过 --json 提供用户列表，或先配置 FEISHU_TEST_USER_ID")

    bot = _get_bot()
    resp = bot.list_freebusy(
        time_min=str(_iso_to_unix_seconds(start_value, "start")),
        time_max=str(_iso_to_unix_seconds(end_value, "end")),
        user_ids=user_ids,
        room_ids=room_ids,
        include_external_calendar=include_external_calendar,
        only_busy=only_busy,
        need_rsvp_status=need_rsvp_status,
        user_id_type=user_id_type,
    )
    if _print_lark_error("查询忙闲", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("忙闲信息获取成功", payload)


# ------------------------------------------------------------------
# chattool lark task
# ------------------------------------------------------------------

@cli.group()
def task():
    """飞书任务工具"""
    pass


@task.command("create")
@click.option("--summary", required=True, help="任务标题")
@click.option("--description", default=None, help="任务描述")
@click.option("--due", default=None, help="截止时间，ISO8601")
@click.option("--all-day", is_flag=True, help="截止时间按全天处理")
@click.option("--members-json", type=click.Path(exists=True, dir_okay=False), default=None,
              help="成员数组 JSON")
@click.option("--add-test-user", is_flag=True, help="将 FEISHU_TEST_USER_ID 作为 assignee 加入任务")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_create(summary, description, due, all_day, members_json, add_test_user, env_ref, user_id_type):
    """创建任务"""
    _load_runtime_env(env_ref)
    members = _require_list_payload(members_json, "members") if members_json else []
    if add_test_user:
        test_member = _get_test_user_member()
        if not test_member:
            raise click.ClickException("未配置 FEISHU_TEST_USER_ID，无法使用 --add-test-user")
        members.append(test_member)

    bot = _get_bot()
    resp = bot.create_task(
        summary=summary,
        description=description,
        due_timestamp=_iso_to_unix_seconds(due, "due") if due else None,
        due_is_all_day=all_day,
        members=members or None,
        user_id_type=user_id_type,
    )
    if _print_lark_error("创建任务", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务创建成功", payload)


@task.command("list")
@click.option("--completed/--open", default=False, help="列出已完成任务或未完成任务")
@click.option("--page-size", type=int, default=50, show_default=True)
@click.option("--page-token", default=None)
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_list(completed, page_size, page_token, env_ref, user_id_type):
    """列出任务"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_tasks(
        completed=completed,
        page_size=page_size,
        page_token=page_token,
        user_id_type=user_id_type,
    )
    if _print_lark_error("列出任务", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务列表获取成功", payload)


@task.command("get")
@click.argument("task_guid")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_get(task_guid, env_ref, user_id_type):
    """获取单个任务"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_task(task_guid, user_id_type=user_id_type)
    if _print_lark_error("获取任务", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务获取成功", payload)


@task.command("patch")
@click.argument("task_guid")
@click.option("--summary", default=None, help="可选：新标题")
@click.option("--description", default=None, help="可选：新描述")
@click.option("--completed-at", default=None, help="完成时间，ISO8601")
@click.option("--due", default=None, help="新截止时间，ISO8601")
@click.option("--all-day", is_flag=True, help="截止时间按全天处理")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_patch(task_guid, summary, description, completed_at, due, all_day, env_ref, user_id_type):
    """更新任务"""
    if not any([summary, description, completed_at, due]):
        raise click.ClickException("请至少提供一个更新项，如 --summary / --description / --completed-at / --due")

    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.patch_task(
        task_guid=task_guid,
        summary=summary,
        description=description,
        completed_at=_iso_to_unix_seconds(completed_at, "completed-at") if completed_at else None,
        due_timestamp=_iso_to_unix_seconds(due, "due") if due else None,
        due_is_all_day=all_day,
        user_id_type=user_id_type,
    )
    if _print_lark_error("更新任务", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务更新成功", payload)


@task.group("tasklist")
def task_tasklist():
    """tasklist 相关命令"""
    pass


@task_tasklist.command("create")
@click.argument("name")
@click.option("--members-json", type=click.Path(exists=True, dir_okay=False), default=None,
              help="成员数组 JSON")
@click.option("--add-test-user", is_flag=True, help="将 FEISHU_TEST_USER_ID 作为成员加入清单")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_tasklist_create(name, members_json, add_test_user, env_ref, user_id_type):
    """创建任务清单"""
    _load_runtime_env(env_ref)
    members = _require_list_payload(members_json, "members") if members_json else []
    if add_test_user:
        test_member = _get_test_user_member()
        if not test_member:
            raise click.ClickException("未配置 FEISHU_TEST_USER_ID，无法使用 --add-test-user")
        members.append(test_member)

    bot = _get_bot()
    resp = bot.create_tasklist(name, members=members or None, user_id_type=user_id_type)
    if _print_lark_error("创建任务清单", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务清单创建成功", payload)


@task_tasklist.command("list")
@click.option("--page-size", type=int, default=50, show_default=True)
@click.option("--page-token", default=None)
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_tasklist_list(page_size, page_token, env_ref, user_id_type):
    """列出任务清单"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_tasklists(page_size=page_size, page_token=page_token, user_id_type=user_id_type)
    if _print_lark_error("列出任务清单", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务清单列表获取成功", payload)


@task_tasklist.command("get")
@click.argument("tasklist_guid")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_tasklist_get(tasklist_guid, env_ref, user_id_type):
    """获取单个任务清单"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_tasklist(tasklist_guid, user_id_type=user_id_type)
    if _print_lark_error("获取任务清单", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务清单获取成功", payload)


@task_tasklist.command("tasks")
@click.argument("tasklist_guid")
@click.option("--completed/--open", default=False, help="列出已完成任务或未完成任务")
@click.option("--page-size", type=int, default=50, show_default=True)
@click.option("--page-token", default=None)
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_tasklist_tasks(tasklist_guid, completed, page_size, page_token, env_ref, user_id_type):
    """列出清单中的任务"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.list_tasklist_tasks(
        tasklist_guid=tasklist_guid,
        completed=completed,
        page_size=page_size,
        page_token=page_token,
        user_id_type=user_id_type,
    )
    if _print_lark_error("列出清单任务", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("清单任务列表获取成功", payload)


@task_tasklist.command("add-members")
@click.argument("tasklist_guid")
@click.option("--json", "json_path", type=click.Path(exists=True, dir_okay=False), default=None,
              help="成员数组 JSON")
@click.option("--add-test-user", is_flag=True, help="将 FEISHU_TEST_USER_ID 作为成员加入清单")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--user-id-type", default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id"], case_sensitive=False))
def task_tasklist_add_members(tasklist_guid, json_path, add_test_user, env_ref, user_id_type):
    """为任务清单添加成员"""
    _load_runtime_env(env_ref)
    members = _require_list_payload(json_path, "members") if json_path else []
    if add_test_user:
        test_member = _get_test_user_member()
        if not test_member:
            raise click.ClickException("未配置 FEISHU_TEST_USER_ID，无法使用 --add-test-user")
        members.append(test_member)
    if not members:
        raise click.ClickException("请通过 --json 提供成员数组，或使用 --add-test-user")

    bot = _get_bot()
    resp = bot.add_tasklist_members(tasklist_guid, members=members, user_id_type=user_id_type)
    if _print_lark_error("添加任务清单成员", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("任务清单成员添加成功", payload)


# ------------------------------------------------------------------
# chattool lark im
# ------------------------------------------------------------------

@cli.group()
def im():
    """飞书消息读取工具"""
    pass


@im.command("list")
@click.option("--chat-id", required=True, help="会话 chat_id")
@click.option("--start-time", default=None, help="开始时间，ISO8601")
@click.option("--end-time", default=None, help="结束时间，ISO8601")
@click.option("--relative-hours", type=int, default=None,
              help="相对当前时间向前回溯 N 小时；未显式传 start/end 时生效")
@click.option("--page-size", type=int, default=20, show_default=True)
@click.option("--page-token", default=None)
@click.option("--sort", "sort_type", default=None, help="透传飞书 sort_type")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def im_list(chat_id, start_time, end_time, relative_hours, page_size, page_token, sort_type, env_ref):
    """按 chat_id 列消息"""
    _load_runtime_env(env_ref)
    if relative_hours is not None and not start_time and not end_time:
        now = int(time.time())
        end_time = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
        start_time = datetime.fromtimestamp(
            now - relative_hours * 3600,
            tz=timezone.utc,
        ).isoformat()

    bot = _get_bot()
    resp = bot.list_messages(
        container_id=chat_id,
        container_id_type="chat",
        start_time=str(_iso_to_unix_seconds(start_time, "start-time")) if start_time else None,
        end_time=str(_iso_to_unix_seconds(end_time, "end-time")) if end_time else None,
        sort_type=sort_type,
        page_size=page_size,
        page_token=page_token,
    )
    if _print_lark_error("列出消息", resp):
        return
    payload = _response_json(resp)
    _print_topic_result("消息列表获取成功", payload)


@im.command("download")
@click.argument("message_id")
@click.argument("file_key")
@click.option("--type", "resource_type", required=True,
              type=click.Choice(["image", "file", "audio", "video"], case_sensitive=False))
@click.option("--output", type=click.Path(dir_okay=False), default=None,
              help="输出文件路径，默认写到当前目录")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def im_download(message_id, file_key, resource_type, output, env_ref):
    """下载消息资源"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_message_resource(message_id, file_key, resource_type.lower())
    if _print_lark_error("下载消息资源", resp):
        return

    output_path = Path(output) if output else Path.cwd() / file_key
    output_path.write_bytes(resp.raw.content)
    click.secho("✅ 资源下载成功", fg="green")
    click.echo(f"path      : {output_path}")
    click.echo(f"bytes     : {len(resp.raw.content)}")


# ------------------------------------------------------------------
# chattool lark troubleshoot
# ------------------------------------------------------------------

@cli.group()
def troubleshoot():
    """飞书排障工具"""
    pass


@troubleshoot.command("check-scopes")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--card-file", type=click.Path(dir_okay=False), default=None,
              help="把权限诊断卡片写到指定 JSON 文件")
@click.option("--send-card", is_flag=True,
              help="将权限诊断卡片直接发送给目标接收者")
@click.option("--receiver", "-r", default=None,
              help="send-card 时的接收者，默认使用 FEISHU_DEFAULT_RECEIVER_ID")
@click.option("--type", "-t", "id_type",
              default="user_id",
              type=click.Choice(["open_id", "user_id", "union_id", "email", "chat_id"]),
              help="send-card 时的接收者 ID 类型 (默认 user_id)")
def troubleshoot_check_scopes(env_ref, card_file, send_card, receiver, id_type):
    """检查关键 scope 分类"""
    _load_runtime_env(env_ref)
    bot = _get_bot()
    resp = bot.get_scopes()
    if not resp.success():
        click.secho(f"❌ 检查 scopes 失败: code={resp.code}  msg={resp.msg}", fg="red")
        return

    granted = _granted_scope_names(resp)
    categories = _scope_category_status(granted)
    missing = [name for name, matches in categories.items() if not matches]
    card = _build_scope_check_card(categories, missing)

    click.secho("✅ scopes 检查完成", fg="green")
    for name, matches in categories.items():
        status = "ok" if matches else "missing"
        click.echo(f"{name:10}: {status} ({len(matches)})")
        for scope in matches[:10]:
            click.echo(f"  - {scope}")
        if len(matches) > 10:
            click.echo(f"  ... (+{len(matches) - 10})")
    if missing:
        click.secho("可能存在权限问题，缺失分类: " + ", ".join(missing), fg="yellow")
        click.echo("建议先在飞书开放平台补齐 scopes，再重新执行相关命令。")
    if card_file:
        Path(card_file).write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        click.echo(f"card_file : {card_file}")
    if send_card:
        target = _resolve_message_receiver(receiver)
        if not target:
            raise click.ClickException("send-card 需要 --receiver，或先配置 FEISHU_DEFAULT_RECEIVER_ID")
        send_resp = bot.send_card(target, id_type, card)
        if _print_lark_error("发送权限诊断卡片", send_resp):
            raise click.Abort()
        click.echo(f"card_message_id: {send_resp.data.message_id}")


@troubleshoot.command("check-events")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def troubleshoot_check_events(env_ref):
    """检查事件订阅相关配置"""
    _load_runtime_env(env_ref)
    click.secho("✅ 事件订阅检查", fg="green")
    click.echo(f"FEISHU_APP_ID         : {'set' if FeishuConfig.FEISHU_APP_ID.value else 'missing'}")
    click.echo(f"FEISHU_APP_SECRET     : {'set' if FeishuConfig.FEISHU_APP_SECRET.value else 'missing'}")
    click.echo(f"FEISHU_ENCRYPT_KEY    : {'set' if FeishuConfig.FEISHU_ENCRYPT_KEY.value else 'missing'}")
    click.echo(f"FEISHU_VERIFY_TOKEN   : {'set' if FeishuConfig.FEISHU_VERIFY_TOKEN.value else 'missing'}")
    click.echo("建议：")
    click.echo("- 长连接调试优先使用 `chattool lark listen`。")
    click.echo("- 若使用 HTTP webhook，再补 FEISHU_ENCRYPT_KEY / FEISHU_VERIFY_TOKEN。")
    click.echo("- 飞书后台需开启事件订阅并发布配置。")


@troubleshoot.command("check-card-action")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def troubleshoot_check_card_action(env_ref):
    """检查卡片交互链路准备情况"""
    _load_runtime_env(env_ref)
    click.secho("✅ 卡片交互检查", fg="green")
    click.echo(f"FEISHU_APP_ID         : {'set' if FeishuConfig.FEISHU_APP_ID.value else 'missing'}")
    click.echo(f"FEISHU_APP_SECRET     : {'set' if FeishuConfig.FEISHU_APP_SECRET.value else 'missing'}")
    click.echo("建议：")
    click.echo("- 确保应用已开通卡片回传能力。")
    click.echo("- 交互卡片消息建议先用 `chattool lark send --card ...` 发送，再观察回调日志。")
    click.echo("- 若回调走 HTTP 模式，需要同步检查事件订阅与 webhook 配置。")


@troubleshoot.command("doctor")
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
def troubleshoot_doctor(env_ref):
    """执行飞书总体诊断"""
    _load_runtime_env(env_ref)
    bot = _get_bot()

    info_resp = bot.get_bot_info()
    if _print_lark_error("获取机器人信息", info_resp):
        return

    info_payload = _response_json(info_resp)
    bot_info = info_payload.get("bot", {})
    activate_status = bot_info.get("activate_status")
    status_map = {1: "未激活", 2: "已激活", 3: "已停用"}

    scopes_resp = bot.get_scopes()
    if not scopes_resp.success():
        click.secho(f"❌ 获取 scopes 失败: code={scopes_resp.code}  msg={scopes_resp.msg}", fg="red")
        return

    granted = _granted_scope_names(scopes_resp)
    categories = _scope_category_status(granted)
    missing = [name for name, matches in categories.items() if not matches]

    click.secho("✅ Feishu doctor", fg="green")
    click.echo(f"bot_name             : {bot_info.get('app_name', '—')}")
    click.echo(f"bot_open_id          : {bot_info.get('open_id', '—')}")
    click.echo(f"activate_status      : {status_map.get(activate_status, '未知')}")
    click.echo(f"granted_scopes       : {len(granted)}")
    for name, matches in categories.items():
        click.echo(f"{name:20}: {'ok' if matches else 'missing'}")
    click.echo(f"default_receiver     : {'set' if FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value else 'missing'}")
    click.echo(f"test_user            : {'set' if FeishuConfig.FEISHU_TEST_USER_ID.value else 'missing'}")
    click.echo(f"encrypt_key          : {'set' if FeishuConfig.FEISHU_ENCRYPT_KEY.value else 'missing'}")
    click.echo(f"verify_token         : {'set' if FeishuConfig.FEISHU_VERIFY_TOKEN.value else 'missing'}")
    if missing:
        click.secho("可能由缺失 scopes 导致的能力问题: " + ", ".join(missing), fg="yellow")


# ------------------------------------------------------------------
# chattool lark listen
# ------------------------------------------------------------------

@cli.command()
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--verbose", "-v", is_flag=True, help="打印完整事件 JSON")
@click.option("--log-level", "-l", default="INFO",
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              help="日志级别 (默认 INFO)")
def listen(env_ref, verbose, log_level):
    """
    启动 WebSocket 监听，打印收到的消息（调试用）。

    \b
    需要先在飞书平台「事件订阅」中开启长连接并订阅 im.message.receive_v1。
    按 Ctrl-C 停止。
    """
    _load_runtime_env(env_ref)
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
    from lark_oapi.ws import Client as WSClient
    
    level_map = {"DEBUG": lark.LogLevel.DEBUG, "INFO": lark.LogLevel.INFO,
                 "WARNING": lark.LogLevel.WARNING, "ERROR": lark.LogLevel.ERROR}
    level = level_map.get(log_level.upper(), lark.LogLevel.INFO)
    lark.logger.setLevel(level.value)

    config = FeishuConfig()
    if not config.FEISHU_APP_ID.value:
        click.secho("FEISHU_APP_ID 未设置", fg="red")
        return

    def on_message(data: P2ImMessageReceiveV1) -> None:
        msg = data.event.message
        sender = data.event.sender
        chat_type_label = "群聊" if msg.chat_type == "group" else "私聊"
        click.echo(
            f"[{chat_type_label}] "
            f"from={sender.sender_id.open_id}  "
            f"type={msg.message_type}  "
            f"chat={msg.chat_id}"
        )
        try:
            content = json.loads(msg.content)
            if msg.message_type == "text":
                click.secho(f"  >> {content.get('text', '')}", fg="cyan")
            elif verbose:
                click.echo(f"  >> {json.dumps(content, ensure_ascii=False)}")
        except Exception:
            pass
        if verbose:
            click.echo(f"  message_id={msg.message_id}")

    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(on_message)
        .build()
    )

    ws = WSClient(
        app_id=config.FEISHU_APP_ID.value,
        app_secret=config.FEISHU_APP_SECRET.value,
        event_handler=handler,
        log_level=level,
    )

    click.secho(f"🔗 启动 WebSocket 监听... log_level={log_level} (Ctrl-C 停止)", fg="green")
    try:
        ws.start()
    except KeyboardInterrupt:
        click.echo("\n已停止")


# ------------------------------------------------------------------
# chattool lark chat
# ------------------------------------------------------------------

@cli.command()
@click.option("--env", "-e", "env_ref", default=None,
              help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--system", "-s", default="你是一个工作助手，回答简洁专业。",
              help="System Prompt")
@click.option("--max-history", "-n", default=10, type=int,
              help="最多保留的对话轮数 (默认 10)")
@click.option("--user", "-u", default="cli_user",
              help="虚拟 user_id，用于会话隔离 (默认 cli_user)")
def chat(env_ref, system, max_history, user):
    """
    在终端启动交互式 AI 对话（经飞书 Bot 透传）。

    \b
    这不通过飞书发送，而是直接在本地终端与 LLM 对话。
    适合快速调试 System Prompt 和对话效果。
    输入 /clear 清除历史，/quit 退出。
    """
    _load_runtime_env(env_ref)

    session = _create_chat_session(system=system, max_history=max_history)
    click.secho(f"💬 AI 对话  (system: {system[:40]}...)", fg="green")
    click.echo("输入 /clear 清除历史，/quit 退出\n")

    while True:
        try:
            text = click.prompt("你", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\n再见！")
            break

        text = text.strip()
        if not text:
            continue
        if text in ("/quit", "/exit", "/q"):
            click.echo("再见！")
            break
        if text == "/clear":
            session.clear(user)
            click.secho("✅ 对话历史已清除", fg="yellow")
            continue

        try:
            reply = session.chat(user, text)
            click.secho(f"AI> {reply}", fg="cyan")
        except Exception as e:
            click.secho(f"⚠️  错误: {e}", fg="red")
