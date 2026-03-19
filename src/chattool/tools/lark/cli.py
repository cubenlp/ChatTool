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
from pathlib import Path
import click
from collections import defaultdict

from chattool.config import BaseEnvConfig, FeishuConfig
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from chattool.tools import LarkBot, ChatSession

@click.group()
def cli():
    """飞书机器人工具"""
    pass


def _resolve_env_path(env_ref: str) -> Path:
    """Resolve an env file path or saved profile name."""
    candidate = Path(env_ref).expanduser()
    if candidate.exists():
        return candidate

    profile_path = CHATTOOL_ENV_DIR / env_ref
    if profile_path.exists():
        return profile_path

    if not profile_path.suffix:
        profile_path = profile_path.with_suffix(".env")
        if profile_path.exists():
            return profile_path

    raise click.ClickException(
        f"未找到配置文件: {env_ref}。可传入 .env 文件路径，或 chatenv 保存的 profile 名称。"
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
    try:
        return LarkBot()
    except Exception as e:
        click.secho(f"初始化失败: {e}", fg="red", err=True)
        click.echo(
            "请确认已设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET，"
            f"或通过 -e/--env 指定配置文件（默认读取 {CHATTOOL_ENV_FILE}）。",
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
    """Read a local text file and convert non-empty lines into paragraphs."""
    if not path:
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.read().splitlines() if line.strip()]


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
            click.echo("  → 提示: 权限不足，请在飞书开放平台申请对应 Scope")
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
@click.option("--open/--no-open", "open_after", default=False,
              help="成功后在本地打开文档链接")
def notify_doc(title, text, env_ref, receiver, id_type, folder_token, append_file, open_after):
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
        append_resp = bot.append_doc_texts(document.document_id, texts=paragraphs)
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
