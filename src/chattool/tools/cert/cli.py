#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSL certificate CLI group for certificate boundary experiments."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import click

from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    ask_select,
    is_interactive_available,
    resolve_command_inputs,
)
from chattool.tools import SSLCertUpdater
from chattool.tools.cert.email import get_git_user_email
from chattool.utils import setup_logger


def _default_email() -> str | None:
    return get_git_user_email()


CERT_APPLY_SCHEMA = CommandSchema(
    name="dns-cert-apply",
    fields=(
        CommandField(
            "domains",
            prompt="domains",
            required=True,
            missing_message="至少需要提供一个域名。",
        ),
        CommandField(
            "email",
            prompt="email",
            required=True,
            default_factory=_default_email,
            missing_message="请通过 --email 指定，或配置 git config user.email。",
        ),
    ),
)


CERT_CHECK_SCHEMA = CommandSchema(
    name="dns-cert-check",
    fields=(
        CommandField(
            "domains",
            prompt="domains",
            required=True,
            missing_message="至少需要提供一个域名。",
        ),
    ),
)


@click.group(name="cert", invoke_without_command=True)
@click.pass_context
def cert_cli(ctx):
    """Manage Let's Encrypt certificates through DNS-01 challenges."""
    if ctx.invoked_subcommand is not None:
        return
    if not is_interactive_available():
        click.echo(ctx.get_help())
        return

    selected = ask_select(
        "选择证书命令",
        choices=[
            "apply - 申请或续期证书",
            "check - 检查本地证书",
        ],
    )
    ctx.invoke(cert_cli.get_command(ctx, selected.split(" - ", 1)[0]))


@cert_cli.command(name="apply")
@click.option(
    "--domain",
    "-d",
    "domains",
    multiple=True,
    required=False,
    help="证书域名，可以指定多个",
)
@click.option("--email", "-e", required=False, help="Let's Encrypt 账户邮箱")
@click.option(
    "--provider",
    "-p",
    default="aliyun",
    type=click.Choice(["aliyun", "tencent"]),
    help="DNS 提供商 (默认: aliyun)",
)
@click.option("--cert-dir", default="certs", help="证书存储根目录，默认 certs")
@click.option("--staging", is_flag=True, help="使用 Let's Encrypt 测试环境")
@click.option("--force", is_flag=True, help="跳过本地过期判断，强制申请/续期")
@click.option("--log-file", default=None, help="日志文件路径，默认不记录到文件")
@click.option(
    "-l",
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="控制证书申请过程的日志级别",
)
@add_interactive_option
def apply(
    domains,
    email,
    provider,
    cert_dir,
    staging,
    force,
    log_file,
    log_level,
    interactive,
):
    """Request or renew SSL certificates."""
    inputs = resolve_command_inputs(
        schema=CERT_APPLY_SCHEMA,
        provided={"domains": tuple(domains), "email": email},
        interactive=interactive,
        usage=(
            "Usage: cert apply -d DOMAIN... "
            "[-e EMAIL] [--provider aliyun|tencent] [-i|-I]"
        ),
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

    click.echo("启动SSL证书更新器...")
    click.echo(f"域名: {', '.join(domains)}")
    click.echo(f"邮箱: {email}")
    click.echo(f"DNS提供商: {provider}")
    click.echo(f"证书存储根目录: {cert_dir}")
    click.echo(f"环境: {'测试' if staging else '生产'}")
    click.echo(f"强制申请/续期: {'是' if force else '否'}")
    click.echo("")

    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        staging=staging,
        force=force,
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


@cert_cli.command(name="check")
@click.option(
    "--domain",
    "-d",
    "domains",
    multiple=True,
    required=False,
    help="要检查的证书域名，可以指定多个",
)
@click.option("--cert-dir", default="certs", help="证书存储根目录，默认 certs")
@click.option("--log-file", default=None, help="日志文件路径，默认不记录到文件")
@click.option(
    "-l",
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="控制证书检查过程的日志级别",
)
@add_interactive_option
def check(domains, cert_dir, log_file, log_level, interactive):
    """Check local certificate files without touching DNS or ACME."""
    inputs = resolve_command_inputs(
        schema=CERT_CHECK_SCHEMA,
        provided={"domains": tuple(domains)},
        interactive=interactive,
        usage="Usage: cert check -d DOMAIN... [--cert-dir PATH] [-i|-I]",
    )
    domains = inputs["domains"]
    if isinstance(domains, str):
        domains = (domains,)

    setup_logger(
        "ssl_cert_checker",
        log_file,
        log_level=str(log_level).upper(),
    )

    cert_root = Path(cert_dir)
    for domain in domains:
        status = inspect_certificate(domain, cert_root)
        _print_cert_status(status)


def inspect_certificate(domain: str, cert_dir: Path) -> dict[str, object]:
    file_domain_name = domain.replace("*", "_")
    domain_dir = cert_dir / file_domain_name
    fullchain_path = domain_dir / "fullchain.pem"
    privkey_path = domain_dir / "privkey.pem"

    status: dict[str, object] = {
        "domain": domain,
        "fullchain": fullchain_path,
        "privkey": privkey_path,
        "exists": fullchain_path.exists() and privkey_path.exists(),
        "expires": None,
        "remaining_days": None,
        "key_match": None,
        "error": None,
    }
    if not status["exists"]:
        return status

    try:
        cert = _load_first_certificate(fullchain_path)
        expires = getattr(cert, "not_valid_after_utc", None)
        if expires is None:
            expires = cert.not_valid_after.replace(tzinfo=timezone.utc)
        remaining = expires - datetime.now(timezone.utc)
        status["expires"] = expires
        status["remaining_days"] = remaining.days
        status["key_match"] = _certificate_key_matches(cert, privkey_path)
    except Exception as exc:
        status["error"] = str(exc)

    return status


def _load_first_certificate(fullchain_path: Path):
    from cryptography import x509

    pem = fullchain_path.read_bytes()
    marker = b"-----END CERTIFICATE-----"
    first_cert = pem.split(marker, 1)[0] + marker + b"\n"
    return x509.load_pem_x509_certificate(first_cert)


def _certificate_key_matches(cert, privkey_path: Path) -> bool:
    from cryptography.hazmat.primitives import serialization

    key_pem = privkey_path.read_bytes()
    private_key = serialization.load_pem_private_key(key_pem, password=None)
    cert_public = cert.public_key()
    key_public = private_key.public_key()

    if type(cert_public) is not type(key_public):
        return False
    try:
        return cert_public.public_numbers() == key_public.public_numbers()
    except AttributeError:
        return False


def _print_cert_status(status: dict[str, object]) -> None:
    click.echo(status["domain"])
    click.echo(f"  fullchain: {status['fullchain']}")
    click.echo(f"  privkey:   {status['privkey']}")
    if not status["exists"]:
        click.echo("  status:    missing")
        return
    if status["error"]:
        click.echo(f"  status:    error: {status['error']}")
        return

    expires = status["expires"]
    if isinstance(expires, datetime):
        click.echo(f"  expires:   {expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        click.echo("  expires:   unknown")
    click.echo(f"  remaining: {status['remaining_days']} days")
    click.echo(f"  key match: {'yes' if status['key_match'] else 'no'}")


main = cert_cli


if __name__ == "__main__":
    cert_cli()
