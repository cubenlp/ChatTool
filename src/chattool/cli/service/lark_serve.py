"""
chattool serve lark — 启动飞书机器人服务

Commands:
    chattool serve lark echo      启动简单回显机器人
    chattool serve lark ai        启动 AI 对话机器人
    chattool serve lark webhook   启动空 Webhook 服务（用于平台验证）
"""
import sys
import click
try:
    from chattool.tools.lark import LarkBot
except Exception as e:
    LarkBot = None


def _get_bot():
    if LarkBot is None:
        click.echo("请确认已设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量", err=True)
        sys.exit(1)


@click.group()
def cli():
    """飞书机器人服务"""
    pass


# ------------------------------------------------------------------
# chattool serve lark echo
# ------------------------------------------------------------------

@cli.command()
@click.option("--mode", "-m", default="ws",
              type=click.Choice(["ws", "flask"]),
              help="运行模式: ws (WebSocket) 或 flask (Webhook)")
@click.option("--host", default="0.0.0.0", help="Flask 监听地址 (仅 flask 模式)")
@click.option("--port", "-p", default=7777, type=int,
              help="Flask 监听端口 (仅 flask 模式)")
def echo(mode, host, port):
    """
    启动回显机器人：原样返回收到的文本消息。

    \b
    适合快速验证消息收发链路是否通畅。

    示例:
      chattool serve lark echo
      chattool serve lark echo --mode flask --port 8080
    """
    bot = _get_bot()

    @bot.on_message
    def handle(ctx):
        ctx.reply(f"Echo: {ctx.text}")

    click.secho(f"🤖 回显机器人启动  mode={mode}", fg="green")
    _start(bot, mode, host, port)


# ------------------------------------------------------------------
# chattool serve lark ai
# ------------------------------------------------------------------

@cli.command()
@click.option("--mode", "-m", default="ws",
              type=click.Choice(["ws", "flask"]),
              help="运行模式")
@click.option("--host", default="0.0.0.0", help="Flask 监听地址")
@click.option("--port", "-p", default=7777, type=int, help="Flask 监听端口")
@click.option("--system", "-s",
              default="你是一个工作助手，回答简洁专业。",
              help="System Prompt")
@click.option("--max-history", "-n", default=10, type=int,
              help="每个用户最多保留的对话轮数")
@click.option("--model", default=None, help="LLM 模型名称 (留空使用默认)")
def ai(mode, host, port, system, max_history, model):
    """
    启动 AI 对话机器人：接入 LLM 进行多轮对话。

    \b
    内置 /clear、/help 命令。

    示例:
      chattool serve lark ai
      chattool serve lark ai --system "你是一名翻译官" --max-history 20
    """
    from chattool.tools.lark.session import ChatSession

    bot = _get_bot()
    session = ChatSession(system=system, max_history=max_history)

    @bot.command("/clear")
    def on_clear(ctx):
        session.clear(ctx.sender_id)
        ctx.reply("对话历史已清除 ✅")

    @bot.command("/help")
    def on_help(ctx):
        ctx.reply(
            "支持的命令:\n"
            "/clear  清除对话历史\n"
            "/help   显示帮助\n"
            "\n直接发消息即可与 AI 对话。"
        )

    @bot.on_message
    def on_msg(ctx):
        if ctx.msg_type != "text":
            ctx.reply("暂只支持文字消息")
            return
        reply_text = session.chat(ctx.sender_id, ctx.text)
        ctx.reply(reply_text)

    click.secho(f"🤖 AI 机器人启动  mode={mode}  system={system[:40]}...", fg="green")
    _start(bot, mode, host, port)


# ------------------------------------------------------------------
# chattool serve lark webhook
# ------------------------------------------------------------------

@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", "-p", default=7777, type=int, help="监听端口")
@click.option("--path", default="/webhook/event", help="Webhook 路径")
@click.option("--encrypt-key", default="", help="事件加密 Key")
@click.option("--verification-token", default="", help="验证 Token")
def webhook(host, port, path, encrypt_key, verification_token):
    """
    启动空 Webhook 服务，用于飞书平台验证 URL。

    \b
    启动后将飞书开放平台的「请求网址 URL」指向
    http://<your_ip>:<port><path>
    平台会发送 challenge 验证请求，此服务自动回复。

    示例:
      chattool serve lark webhook
      chattool serve lark webhook --port 8080 --path /lark/events
    """
    bot = _get_bot()
    click.secho(
        f"🔗 Webhook 服务启动  http://{host}:{port}{path}",
        fg="green",
    )
    bot.start(
        mode="flask",
        encrypt_key=encrypt_key,
        verification_token=verification_token,
        host=host,
        port=port,
        path=path,
    )


def _start(bot, mode, host, port):
    try:
        if mode == "ws":
            bot.start(mode="ws")
        else:
            bot.start(mode="flask", host=host, port=port)
    except KeyboardInterrupt:
        click.echo("\n已停止")
