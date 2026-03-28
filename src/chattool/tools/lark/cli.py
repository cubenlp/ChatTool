"""Minimal ChatTool Lark CLI.

ChatTool now keeps only the small helper surface that is still specific to the
repo, while the broader Feishu/Lark command surface is delegated to the
official `lark-cli`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from chattool.cli_warnings import install_cli_warning_filters
from chattool.config import BaseEnvConfig, FeishuConfig
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE

install_cli_warning_filters()


@click.group()
def cli():
    """ChatTool retained Lark helpers: info / send / chat."""
    pass


def _resolve_env_path(env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate

    profile_path = FeishuConfig.get_profile_env_file(CHATTOOL_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path

    raise click.ClickException(
        f"未找到配置文件: {env_ref}。可传入 .env 文件路径，或 Feishu 类型下保存的 profile 名称。"
    )


def _load_runtime_env(env_ref: str | None) -> Path | None:
    if not env_ref:
        return None

    env_path = _resolve_env_path(env_ref)
    BaseEnvConfig.load_all_with_override(
        CHATTOOL_ENV_DIR,
        override_env_file=env_path,
        legacy_env_file=CHATTOOL_ENV_FILE,
    )
    return env_path


def _get_bot():
    from chattool.tools.lark.bot import LarkBot

    try:
        return LarkBot()
    except Exception as e:
        click.secho(f"初始化失败: {e}", fg="red", err=True)
        click.echo(
            "请确认已设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET，"
            f"或通过 -e/--env 指定配置文件（默认读取 {CHATTOOL_ENV_DIR / FeishuConfig.get_storage_name() / '.env'}）。",
            err=True,
        )
        sys.exit(1)


def _resolve_text_target(receiver: str | None, text: str | None) -> tuple[str | None, str | None]:
    default_receiver = FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value or None

    if receiver and text:
        return receiver, text
    if receiver and not text and default_receiver:
        return default_receiver, receiver
    if not receiver and text and default_receiver:
        return default_receiver, text
    return receiver, text


def _create_chat_session(*, system: str = "", max_history: int | None = None):
    from chattool.tools.lark.session import ChatSession

    return ChatSession(system=system, max_history=max_history)


@cli.command()
@click.option("--env", "-e", "env_ref", default=None, help="从指定 .env 文件或已保存 profile 读取配置")
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


@cli.command()
@click.argument("receiver", required=False)
@click.argument("text", required=False, default="")
@click.option("--env", "-e", "env_ref", default=None, help="从指定 .env 文件或已保存 profile 读取配置")
@click.option(
    "--type",
    "-t",
    "id_type",
    default="user_id",
    type=click.Choice(["open_id", "user_id", "union_id", "email", "chat_id"]),
    help="接收者 ID 类型 (默认 user_id)",
)
def send(receiver, text, env_ref, id_type):
    """发送一条文本消息。

    示例:
      chattool lark send "你好"
      chattool lark send f25gc16d "你好"
      chattool lark send oc_xxx "群通知" -t chat_id
    """
    _load_runtime_env(env_ref)
    bot = _get_bot()
    receiver, text = _resolve_text_target(receiver, text)

    if receiver and not text:
        click.secho(
            "单参数形式需要先配置 FEISHU_DEFAULT_RECEIVER_ID；否则请显式传入 receiver 和 text",
            fg="red",
        )
        return
    if not receiver:
        click.secho("请指定接收者，或先配置 FEISHU_DEFAULT_RECEIVER_ID 作为默认发送目标", fg="red")
        return
    if not text:
        click.secho("请提供文本消息内容", fg="red")
        return

    resp = bot.send_text(receiver, id_type, text)
    if resp.success():
        click.secho(f"✅ 文本消息发送成功  message_id={resp.data.message_id}", fg="green")
        return

    click.secho(f"❌ 发送失败: code={resp.code}  msg={resp.msg}", fg="red")
    if resp.code == 99991663:
        click.echo("  → 提示: 用户不在应用可见范围内")


@cli.command()
@click.option("--env", "-e", "env_ref", default=None, help="从指定 .env 文件或已保存 profile 读取配置")
@click.option("--system", "-s", default="你是一个工作助手，回答简洁专业。", help="System Prompt")
@click.option("--max-history", "-n", default=10, type=int, help="最多保留的对话轮数 (默认 10)")
@click.option("--user", "-u", default="cli_user", help="虚拟 user_id，用于会话隔离 (默认 cli_user)")
def chat(env_ref, system, max_history, user):
    """在终端启动交互式 AI 对话。"""
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
