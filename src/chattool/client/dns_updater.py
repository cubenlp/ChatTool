#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新 CLI
"""

import click
import asyncio
from chattool.utils import setup_logger
from chattool.tools.dns.dynamic_ip_updater import DynamicIPUpdater, LOG_FILE
from chattool.tools.dns.utils import create_dns_client

# CLI 接口
@click.group()
def cli():
    """DNSPod动态IP更新工具"""
    pass

@cli.command()
@click.argument('full_domain', required=True)
@click.option('--ttl', default=600, help='TTL值 (默认: 600)')
@click.option('--interval', '-i', default=120, help='检查间隔秒数 (默认: 120)')
@click.option('--max-retries', default=3, help='最大重试次数 (默认: 3)')
@click.option('--retry-delay', default=5, help='重试延迟秒数 (默认: 5)')
@click.option('--monitor', is_flag=True, help='持续监控IP变化')
@click.option('--log-file', help='日志文件路径')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
@click.option('--ip-type', default='public', type=click.Choice(['public', 'local']), help='IP类型 (默认: public)')
@click.option('--local-ip-cidr', help='局域网IP过滤网段 (例如: 192.168.0.0/16)，仅当 ip-type=local 时有效')
def ddns(full_domain, ttl, interval, max_retries, retry_delay, monitor, log_file, log_level, ip_type, local_ip_cidr):
    """执行动态DNS更新（支持一次性或持续监控）
    
    使用完整的域名作为参数:
        chattool dns ddns public.rexwang.site
    """
    record_type = 'A'
    
    # 解析 full_domain
    parts = full_domain.split('.')
    if len(parts) < 2:
        click.echo("错误: 无效的完整域名格式。应如 'sub.example.com'", err=True)
        exit(1)
    
    domain = ".".join(parts[-2:])
    rr_parts = parts[:-2]
    if not rr_parts:
        rr = "@"
    else:
        rr = ".".join(rr_parts)
            
    # 设置日志
    logger = setup_logger(
        name="dns_updater",
        log_file=log_file or LOG_FILE if monitor else None,
        log_level=log_level,
        format_type="detailed" if monitor else "simple"
    )
    
    # 创建更新器
    updater = DynamicIPUpdater(
        domain_name=domain,
        rr=rr,
        record_type=record_type,
        dns_ttl=ttl,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger,
        ip_type=ip_type,
        local_ip_cidr=local_ip_cidr
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
                exit(1)
    except KeyboardInterrupt:
        if monitor:
            logger.info("监控已停止")
        else:
            logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"运行失败: {e}")
        exit(1)

@cli.command(name='list')
@click.option('--domain', '-d', required=True, help='域名')
@click.option('--rr', '-r', help='主机记录过滤')
@click.option('--type', '-t', 'record_type', help='记录类型过滤')
@click.option('--provider', '-p', default='tencent', type=click.Choice(['aliyun', 'tencent']), help='DNS提供商 (默认: tencent)')
def list_records(domain, rr, record_type, provider):
    """列出DNS记录"""
    
    logger = setup_logger("dns_list", log_level="INFO", format_type="simple")
    
    try:
        client = create_dns_client(provider, logger=logger)
        records = client.describe_domain_records(
            domain_name=domain,
            subdomain=rr,
            record_type=record_type
        )
        
        if records:
            click.echo(f"域名 {domain} 的DNS记录:")
            click.echo("-" * 80)
            click.echo(f"{'记录ID':<10} {'主机记录':<15} {'类型':<8} {'值':<25} {'TTL':<8} {'状态':<8}")
            click.echo("-" * 80)
            
            for record in records:
                click.echo(f"{record['RecordId']:<10} {record['RR']:<15} {record['Type']:<8} {record['Value']:<25} {record['TTL']:<8} {record['Status']:<8}")
        else:
            click.echo(f"未找到域名 {domain} 的DNS记录")
            
    except Exception as e:
        logger.error(f"列出DNS记录失败: {e}")
        exit(1)

if __name__ == '__main__':
    cli()
