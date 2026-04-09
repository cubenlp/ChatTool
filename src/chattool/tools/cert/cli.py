#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL证书自动更新 CLI
"""

import click
import asyncio
from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)
from chattool.utils import setup_logger
from chattool.tools import SSLCertUpdater


CERT_UPDATE_SCHEMA = CommandSchema(
    name="dns-cert-update",
    fields=(
        CommandField(
            "domains",
            prompt="domains",
            required=True,
            missing_message="至少需要提供一个域名。",
        ),
        CommandField("email", prompt="email", required=True),
    ),
)


# 命令行入口
@click.command()
@click.option(
    "--domains", "-d", multiple=True, required=False, help="域名列表，可以指定多个"
)
@click.option("--email", "-e", required=False, help="Let's Encrypt账户邮箱")
@click.option(
    "--provider",
    "-p",
    default="aliyun",
    type=click.Choice(["aliyun", "tencent"]),
    help="DNS提供商 (默认: aliyun)",
)
@click.option("--cert-dir", default="certs", help=f"证书存储根目录，默认 certs")
@click.option("--staging", is_flag=True, help="使用Let's Encrypt测试环境")
@click.option("--log-file", default=None, help=f"日志文件路径，默认不记录到文件")
@click.option(
    "-l",
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="控制证书更新过程的日志级别",
)
@add_interactive_option
def main(domains, email, provider, cert_dir, staging, log_file, log_level, interactive):
    """SSL 证书自动更新工具

    使用 Let's Encrypt 和 DNS API 自动申请和更新 SSL 证书。
    证书将保存在 <cert-dir>/<domain>/ 目录下，包含:
    - fullchain.pem: 完整证书链 (Nginx使用)
    - privkey.pem: 私钥 (Nginx使用)
    - cert.pem: 叶子证书
    - chain.pem: 中间证书

    示例:

    chattool dns cert-update -d example.com -e admin@example.com -p tencent
    """
    inputs = resolve_command_inputs(
        schema=CERT_UPDATE_SCHEMA,
        provided={"domains": tuple(domains), "email": email},
        interactive=interactive,
        usage="Usage: chattool dns cert-update -d DOMAIN... -e EMAIL [-i|-I]",
    )
    domains = inputs["domains"]
    if isinstance(domains, str):
        domains = (domains,)
    email = inputs["email"]

    logger = setup_logger(
        "ssl_cert_updater",
        log_file,
        log_level=str(log_level).upper(),
    )

    click.echo(f"启动SSL证书更新器...")
    click.echo(f"域名: {', '.join(domains)}")
    click.echo(f"邮箱: {email}")
    click.echo(f"DNS提供商: {provider}")
    click.echo(f"证书存储根目录: {cert_dir}")
    click.echo(f"环境: {'测试' if staging else '生产'}")
    click.echo("")

    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        staging=staging,
        logger=logger,
        dns_type=provider,
    )

    try:
        result = asyncio.run(updater.run_once())
        if result:
            click.echo("SSL证书更新成功")
        else:
            click.echo("SSL证书更新失败", err=True)
            raise click.Abort()
    except KeyboardInterrupt:
        click.echo("\n程序被用户中断")
    except Exception as e:
        click.echo(f"程序运行出错: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
