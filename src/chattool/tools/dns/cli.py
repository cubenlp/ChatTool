#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新 CLI
"""

import os
import click
import asyncio

from chattool.interaction import (
    ask_select,
    CommandConstraint,
    CommandField,
    CommandSchema,
    add_interactive_option,
    is_interactive_available,
    resolve_command_inputs,
)
from chattool.utils import setup_logger
from chattool.tools import DynamicIPUpdater, create_dns_client
from chattool.tools.dns.domain_utils import split_full_domain


# CLI 接口
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """DNS helpers for dynamic IP updates and record management."""
    if ctx.invoked_subcommand is not None:
        return
    if not is_interactive_available():
        click.echo(ctx.get_help())
        return

    selected = ask_select(
        "选择 DNS 命令",
        choices=[
            "ddns - 动态更新 DNS 记录",
            "set - 创建或更新 DNS 记录",
            "get - 查询 DNS 记录",
            "cert-update - 申请或更新证书",
        ],
    )
    ctx.invoke(cli.get_command(ctx, selected.split(" - ", 1)[0]))


def _resolve_domain_inputs(full_domain, domain, rr):
    if full_domain:
        if domain or rr:
            click.echo(
                "警告: 当提供 full_domain 时，--domain 和 --rr 参数将被忽略。", err=True
            )

        try:
            return split_full_domain(full_domain)
        except ValueError as exc:
            raise click.ClickException(
                "无效的完整域名格式。应如 'sub.example.com'"
            ) from exc

    return domain, rr


def _validate_dns_domain_pair(values):
    if values.get("domain") and values.get("rr"):
        return None
    return "必须提供 full_domain 位置参数，或者同时提供 --domain 和 --rr 选项。"


def _validate_dns_domain_only(values):
    if values.get("domain"):
        return None
    return "必须提供域名。"


DNS_PAIR_SCHEMA = CommandSchema(
    name="dns-domain-pair",
    fields=(
        CommandField(
            "domain",
            prompt="domain",
            required=True,
            missing_message="必须提供 full_domain 位置参数，或者同时提供 --domain 和 --rr 选项。",
        ),
        CommandField(
            "rr",
            prompt="rr",
            required=True,
            default="@",
            prompt_if_missing=True,
            missing_message="必须提供 full_domain 位置参数，或者同时提供 --domain 和 --rr 选项。",
        ),
    ),
    constraints=(CommandConstraint(_validate_dns_domain_pair),),
)


DNS_SET_SCHEMA = CommandSchema(
    name="dns-set",
    fields=(
        CommandField(
            "domain",
            prompt="domain",
            required=True,
            missing_message="必须提供 full_domain 或同时提供 -d 和 -r，并指定 --value。",
        ),
        CommandField(
            "rr",
            prompt="rr",
            required=True,
            default="@",
            prompt_if_missing=True,
            missing_message="必须提供 full_domain 或同时提供 -d 和 -r，并指定 --value。",
        ),
        CommandField(
            "value",
            prompt="value",
            required=True,
            missing_message="必须提供 full_domain 或同时提供 -d 和 -r，并指定 --value。",
        ),
    ),
    constraints=(CommandConstraint(_validate_dns_domain_pair),),
)


DNS_GET_SCHEMA = CommandSchema(
    name="dns-get",
    fields=(
        CommandField(
            "domain", prompt="domain", required=True, missing_message="必须提供域名。"
        ),
        CommandField("rr", prompt="rr", default="@", prompt_if_missing=True),
    ),
    constraints=(CommandConstraint(_validate_dns_domain_only),),
)


@cli.command()
@click.argument("full_domain", required=False)
@click.option("--domain", "-d", help="域名 (如 rexwang.site)")
@click.option("--rr", "-r", help="主机记录 (如 www, @)")
@click.option("--ttl", default=600, help="TTL值 (默认: 600)")
@click.option("--interval", default=120, help="检查间隔秒数 (默认: 120)")
@click.option("--max-retries", default=3, help="最大重试次数 (默认: 3)")
@click.option("--retry-delay", default=5, help="重试延迟秒数 (默认: 5)")
@click.option("--monitor", is_flag=True, help="持续监控IP变化")
@click.option(
    "--log-file",
    default=None,
    help="日志文件路径 (默认不记录到文件，除非开启监控模式且未指定则使用默认)",
)
@click.option("--log-level", default="INFO", help="日志级别 (默认: INFO)")
@click.option(
    "--ip-type",
    default="public",
    type=click.Choice(["public", "local"]),
    help="IP类型 (默认: public)",
)
@click.option(
    "--local-ip-cidr",
    help="局域网IP过滤网段 (例如: 192.168.0.0/16)，仅当 ip-type=local 时有效",
)
@click.option(
    "--provider",
    "-p",
    default="aliyun",
    type=click.Choice(["aliyun", "tencent"]),
    help="DNS提供商 (默认: aliyun)",
)
@add_interactive_option
def ddns(
    full_domain,
    domain,
    rr,
    ttl,
    interval,
    max_retries,
    retry_delay,
    monitor,
    log_file,
    log_level,
    ip_type,
    local_ip_cidr,
    provider,
    interactive,
):
    """Run dynamic DNS updates once or in continuous monitoring mode.

    支持两种参数方式:
    1. 完整域名位置参数:
       chattool dns ddns public.rexwang.site

    2. 分别指定域名和记录 (通用模式):
       chattool dns ddns -d rexwang.site -r public
    """
    record_type = "A"

    domain, rr = _resolve_domain_inputs(full_domain, domain, rr)
    inputs = resolve_command_inputs(
        schema=DNS_PAIR_SCHEMA,
        provided={"domain": domain, "rr": rr},
        interactive=interactive,
        usage="Usage: chattool dns ddns [FULL_DOMAIN] [--domain TEXT] [--rr TEXT] [--provider aliyun|tencent] [-i|-I]",
    )
    domain = inputs["domain"]
    rr = inputs["rr"]

    # 设置日志
    # 如果开启监控且未指定log_file，使用默认 LOG_FILE (定义在本地，或 ip_updater)
    # 由于我们从 ip_updater 移除了默认 LOG_FILE，我们在 CLI 这里定义默认值
    DEFAULT_LOG_FILE = "dynamic_ip_updater.log"

    actual_log_file = log_file
    if monitor and not actual_log_file:
        actual_log_file = DEFAULT_LOG_FILE

    logger = setup_logger(
        name="dns_updater",
        log_file=actual_log_file,
        log_level=log_level,
        format_type="detailed" if monitor else "simple",
    )

    # 创建更新器
    updater = DynamicIPUpdater(
        domain_name=domain,
        rr=rr,
        dns_type=provider,
        record_type=record_type,
        dns_ttl=ttl,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger,
        log_file=actual_log_file,
        ip_type=ip_type,
        local_ip_cidr=local_ip_cidr,
    )

    try:
        if monitor:
            # 运行持续监控
            asyncio.run(updater.run_continuous(interval))
        else:
            # 执行一次更新
            success = asyncio.run(updater.run_once())
            if success:
                logger.info("DNS更新完成")
            else:
                logger.error("DNS更新失败")
                raise click.ClickException("DNS更新失败")
    except KeyboardInterrupt:
        if monitor:
            logger.info("监控已停止")
        else:
            logger.info("程序被用户中断")
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"运行失败: {e}")
        raise click.ClickException(f"运行失败: {e}")


@cli.command(name="set")
@click.argument("full_domain", required=False)
@click.option("--domain", "-d", help="域名")
@click.option("--rr", "-r", help="主机记录")
@click.option("--type", "-t", "record_type", default="A", help="记录类型 (默认: A)")
@click.option("--value", "-v", required=False, help="记录值")
@click.option("--ttl", default=600, help="TTL值 (默认: 600)")
@click.option(
    "--provider",
    "-p",
    default="aliyun",
    type=click.Choice(["aliyun", "tencent"]),
    help="DNS提供商 (默认: aliyun)",
)
@add_interactive_option
def set_record(full_domain, domain, rr, record_type, value, ttl, provider, interactive):
    """Create or update a DNS record.

    支持:
    1. 完整域名: chattool dns set test.example.com -v 1.2.3.4
    2. 分开指定: chattool dns set -d example.com -r test -v 1.2.3.4
    """
    domain, rr = _resolve_domain_inputs(full_domain, domain, rr)
    inputs = resolve_command_inputs(
        schema=DNS_SET_SCHEMA,
        provided={"domain": domain, "rr": rr, "value": value},
        interactive=interactive,
        usage="Usage: chattool dns set [FULL_DOMAIN] [--domain TEXT] [--rr TEXT] --value TEXT [--provider aliyun|tencent] [-i|-I]",
    )
    domain = inputs["domain"]
    rr = inputs["rr"]
    value = inputs["value"]

    logger = setup_logger("dns_set", log_level="INFO", format_type="simple")
    try:
        client = create_dns_client(provider, logger=logger)

        # 检查是否存在
        records = client.describe_domain_records(
            domain, subdomain=rr, record_type=record_type
        )

        if records:
            logger.info(f"删除记录 {rr}.{domain} ({record_type}) -> {value}")
            client.delete_record_value(domain, rr, record_type)

        logger.info(f"添加记录 {rr}.{domain} ({record_type}) -> {value}")
        res = client.add_domain_record(domain, rr, record_type, value, ttl)
        if res:
            click.echo(f"操作成功: {rr}.{domain} -> {value}")
        else:
            raise click.ClickException("操作失败")

    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"设置DNS记录失败: {e}")
        raise click.ClickException(f"设置DNS记录失败: {e}")


@cli.command(name="get")
@click.argument("full_domain", required=False)
@click.option("--domain", "-d", help="域名")
@click.option("--rr", "-r", help="主机记录")
@click.option("--type", "-t", "record_type", help="记录类型过滤")
@click.option(
    "--provider",
    "-p",
    default="aliyun",
    type=click.Choice(["aliyun", "tencent"]),
    help="DNS提供商 (默认: aliyun)",
)
@add_interactive_option
def get_record(full_domain, domain, rr, record_type, provider, interactive):
    """Show DNS record details.

    支持:
    1. 完整域名: chattool dns get test.example.com
    2. 分开指定: chattool dns get -d example.com -r test
    """
    domain, rr = _resolve_domain_inputs(full_domain, domain, rr)
    inputs = resolve_command_inputs(
        schema=DNS_GET_SCHEMA,
        provided={"domain": domain, "rr": rr},
        interactive=interactive,
        usage="Usage: chattool dns get [FULL_DOMAIN] [--domain TEXT] [--rr TEXT] [--provider aliyun|tencent] [-i|-I]",
    )
    domain = inputs["domain"]
    rr = inputs["rr"]

    logger = setup_logger("dns_get", log_level="INFO", format_type="simple")
    try:
        client = create_dns_client(provider, logger=logger)
        records = client.describe_domain_records(
            domain, subdomain=rr, record_type=record_type
        )

        if records:
            click.echo(f"DNS记录 ({provider}):")
            click.echo(
                f"{'ID':<20} {'RR':<15} {'Type':<8} {'Value':<30} {'TTL':<6} {'Status'}"
            )
            click.echo("-" * 90)
            for r in records:
                click.echo(
                    f"{r['RecordId']:<20} {r['RR']:<15} {r['Type']:<8} {r['Value']:<30} {r['TTL']:<6} {r.get('Status', '-')}"
                )
        else:
            click.echo("未找到匹配的记录")

    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"获取DNS记录失败: {e}")
        raise click.ClickException(f"获取DNS记录失败: {e}")


@cli.command(name="hook-auth", hidden=True)
def hook_auth():
    """Certbot manual auth hook"""
    # Certbot passes validation info via environment variables
    domain = os.environ.get("CERTBOT_DOMAIN")
    validation = os.environ.get("CERTBOT_VALIDATION")

    if not domain or not validation:
        click.echo("Error: CERTBOT_DOMAIN or CERTBOT_VALIDATION not set", err=True)
        exit(1)

    logger = setup_logger("certbot_hook", log_level="INFO", format_type="simple")
    logger.info(f"Auth hook called for {domain}")

    # We need to add _acme-challenge.{domain} TXT record
    # Similar logic to DynamicIPUpdater but for TXT record

    # Parse domain to find main domain
    # Simple heuristic: last 2 parts
    parts = domain.split(".")
    main_domain = ".".join(parts[-2:])

    if domain == main_domain:
        rr = "_acme-challenge"
    else:
        # e.g. *.local.rexwang.site -> domain=rexwang.site
        # CERTBOT_DOMAIN might be "local.rexwang.site" (without *)
        # or "www.example.com" -> rr="_acme-challenge.www"
        prefix = domain[: -len(main_domain) - 1]
        rr = f"_acme-challenge.{prefix}"

    try:
        # Auto-detect provider or default to tencent (can be configured via env if needed)
        # For now, let's try to load from config or default to tencent as per other commands
        # Ideally, we should check which provider manages this domain.
        # But we'll stick to 'tencent' default or env config if we had one.
        # Let's use 'tencent' as default for now since previous tests used it.
        # IMPROVEMENT: Add logic to try both or config.
        provider = os.environ.get("CHATTOOL_DNS_PROVIDER", "tencent")

        client = create_dns_client(provider, logger=logger)

        # Add TXT record
        # We use add_domain_record directly
        # First check if exists? Certbot might call multiple times.
        # Just add it.

        logger.info(f"Adding TXT record: {rr}.{main_domain} -> {validation}")

        # Note: Some providers might take time. Certbot waits for us to return.
        # We just add the record. Certbot will wait before verification.

        client.add_domain_record(
            domain_name=main_domain, rr=rr, type_="TXT", value=validation, ttl=120
        )

        # Wait a bit for propagation locally? No, Certbot handles waiting if we just return.
        # But usually manual hooks are immediate.
        import time

        time.sleep(5)  # Safety buffer

    except Exception as e:
        logger.error(f"Auth hook failed: {e}")
        exit(1)


@cli.command(name="hook-cleanup", hidden=True)
def hook_cleanup():
    """Certbot manual cleanup hook"""
    domain = os.environ.get("CERTBOT_DOMAIN")

    if not domain:
        return

    logger = setup_logger("certbot_hook", log_level="INFO", format_type="simple")
    logger.info(f"Cleanup hook called for {domain}")

    parts = domain.split(".")
    main_domain = ".".join(parts[-2:])

    if domain == main_domain:
        rr = "_acme-challenge"
    else:
        prefix = domain[: -len(main_domain) - 1]
        rr = f"_acme-challenge.{prefix}"

    try:
        provider = os.environ.get("CHATTOOL_DNS_PROVIDER", "tencent")
        client = create_dns_client(provider, logger=logger)

        logger.info(f"Deleting TXT record: {rr}.{main_domain}")
        client.delete_subdomain_records(main_domain, rr)

    except Exception as e:
        logger.error(f"Cleanup hook failed: {e}")
        # Don't fail the cert process for cleanup failure
        pass


if __name__ == "__main__":
    cli()
