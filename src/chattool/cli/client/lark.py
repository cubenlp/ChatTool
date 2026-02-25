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
import sys
import click
from collections import defaultdict

from chattool.config import FeishuConfig
from chattool.tools import LarkBot, ChatSession

@click.group()
def cli():
    """飞书机器人工具"""
    pass


def _get_bot():
    """Lazy-init a LarkBot from env vars."""
    try:
        return LarkBot()
    except Exception as e:
        click.secho(f"初始化失败: {e}", fg="red", err=True)
        click.echo("请确认已设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量", err=True)
        sys.exit(1)


# ------------------------------------------------------------------
# chattool lark info
# ------------------------------------------------------------------

@cli.command()
def info():
    """获取机器人基本信息（验证凭证）"""
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
@click.option("--all", "-a", "show_all", is_flag=True,
              help="显示全部权限（包括未授权的）")
@click.option("--filter", "-f", "keyword", default=None,
              help="按关键字过滤 (如 im, calendar, drive)")
@click.option("--group", "-g", is_flag=True,
              help="按模块分组显示")
def scopes(show_all, keyword, group):
    """查看应用已申请的权限列表"""
    bot = _get_bot()
    resp = bot.get_scopes()

    if not resp.success():
        click.secho(f"请求失败: code={resp.code}  msg={resp.msg}", fg="red")
        return

    scope_list = resp.data.scopes or []
    if not scope_list:
        click.echo("未找到任何权限记录")
        return

    if not show_all:
        scope_list = [s for s in scope_list if s.grant_status == 1]

    if keyword:
        kw = keyword.lower()
        scope_list = [s for s in scope_list if kw in (s.scope_name or "").lower()]

    if not scope_list:
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


# ------------------------------------------------------------------
# chattool lark send
# ------------------------------------------------------------------

@cli.command()
@click.argument("receiver")
@click.argument("text", default="")
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
def send(receiver, text, id_type, image_path, file_path, card_file, post_file):
    """
    发送消息给指定用户或群。

    \b
    示例:
      chattool lark send rexwzh "你好，世界"
      chattool lark send rexwzh --image photo.jpg
      chattool lark send rexwzh --file report.pdf
      chattool lark send rexwzh --card card.json
      chattool lark send oc_xxx "群消息" -t chat_id
    """
    bot = _get_bot()

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
            click.echo("  → 提示: 权限不足，请在飞书开放平台申请对应 Scope")
        elif resp.code == 99991663:
            click.echo("  → 提示: 用户不在应用可见范围内")


# ------------------------------------------------------------------
# chattool lark upload
# ------------------------------------------------------------------

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--type", "-t", "upload_type", default="auto",
              type=click.Choice(["auto", "image", "file"]),
              help="上传类型 (默认 auto，根据扩展名判断)")
def upload(path, upload_type):
    """
    上传图片或文件到飞书，返回 image_key / file_key。

    \b
    示例:
      chattool lark upload photo.jpg
      chattool lark upload report.pdf
      chattool lark upload data.bin -t file
    """
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
def reply(message_id, text):
    """
    引用回复一条消息。

    \b
    示例:
      chattool lark reply om_xxx "收到，已处理"
    """
    bot = _get_bot()
    resp = bot.reply(message_id, text)
    if resp.success():
        click.secho(f"✅ 回复成功  message_id={resp.data.message_id}", fg="green")
    else:
        click.secho(f"❌ 回复失败: code={resp.code}  msg={resp.msg}", fg="red")


# ------------------------------------------------------------------
# chattool lark listen
# ------------------------------------------------------------------

@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="打印完整事件 JSON")
@click.option("--log-level", "-l", default="INFO",
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              help="日志级别 (默认 INFO)")
def listen(verbose, log_level):
    """
    启动 WebSocket 监听，打印收到的消息（调试用）。

    \b
    需要先在飞书平台「事件订阅」中开启长连接并订阅 im.message.receive_v1。
    按 Ctrl-C 停止。
    """
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
@click.option("--system", "-s", default="你是一个工作助手，回答简洁专业。",
              help="System Prompt")
@click.option("--max-history", "-n", default=10, type=int,
              help="最多保留的对话轮数 (默认 10)")
@click.option("--user", "-u", default="cli_user",
              help="虚拟 user_id，用于会话隔离 (默认 cli_user)")
def chat(system, max_history, user):
    """
    在终端启动交互式 AI 对话（经飞书 Bot 透传）。

    \b
    这不通过飞书发送，而是直接在本地终端与 LLM 对话。
    适合快速调试 System Prompt 和对话效果。
    输入 /clear 清除历史，/quit 退出。
    """
    

    session = ChatSession(system=system, max_history=max_history)
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
