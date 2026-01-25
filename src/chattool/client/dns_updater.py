#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新 CLI
"""

import click
import asyncio
from chattool.utils import setup_logger
from chattool.tools.dns.dynamic_ip_updater import DynamicIPUpdater, LOG_FILE
from chattool.tools.dns.tencent import TencentDNSClient

# CLI 接口
@click.group()
def cli():
    """DNSPod动态IP更新工具"""
    pass

@cli.command()
@click.option('--domain', '-d', required=True, help='域名')
@click.option('--rr', '-r', required=True, help='主机记录 (如 www, @, *)')
@click.option('--type', '-t', 'record_type', default='A', help='记录类型 (默认: A)')
@click.option('--ttl', default=600, help='TTL值 (默认: 600)')
@click.option('--interval', '-i', default=120, help='检查间隔秒数 (默认: 120)')
@click.option('--max-retries', default=3, help='最大重试次数 (默认: 3)')
@click.option('--retry-delay', default=5, help='重试延迟秒数 (默认: 5)')
@click.option('--log-file', help='日志文件路径')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
def monitor(domain, rr, record_type, ttl, interval, max_retries, retry_delay, log_file, log_level):
    """持续监控IP变化并自动更新DNS记录"""
    
    # 设置日志
    logger = setup_logger(
        name="tencent_dns_monitor",
        log_file=log_file or LOG_FILE,
        log_level=log_level,
        format_type="detailed"
    )
    
    # 创建更新器
    updater = DynamicIPUpdater(
        domain_name=domain,
        rr=rr,
        record_type=record_type,
        dns_ttl=ttl,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger
    )
    
    # 运行持续监控
    try:
        asyncio.run(updater.run_continuous(interval))
    except KeyboardInterrupt:
        logger.info("监控已停止")
    except Exception as e:
        logger.error(f"监控运行失败: {e}")

@cli.command()
@click.option('--domain', '-d', required=True, help='域名')
@click.option('--rr', '-r', required=True, help='主机记录 (如 www, @, *)')
@click.option('--type', '-t', 'record_type', default='A', help='记录类型 (默认: A)')
@click.option('--ttl', default=600, help='TTL值 (默认: 600)')
@click.option('--max-retries', default=3, help='最大重试次数 (默认: 3)')
@click.option('--retry-delay', default=5, help='重试延迟秒数 (默认: 5)')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
def update(domain, rr, record_type, ttl, max_retries, retry_delay, log_level):
    """执行一次IP检查和DNS更新"""
    
    # 设置日志
    logger = setup_logger(
        name="tencent_dns_update",
        log_level=log_level,
        format_type="simple"
    )
    
    # 创建更新器
    updater = DynamicIPUpdater(
        domain_name=domain,
        rr=rr,
        record_type=record_type,
        dns_ttl=ttl,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger
    )
    
    # 执行一次更新
    try:
        success = asyncio.run(updater.run_once())
        if success:
            logger.info("DNS更新完成")
        else:
            logger.error("DNS更新失败")
            exit(1)
    except Exception as e:
        logger.error(f"DNS更新失败: {e}")
        exit(1)

@cli.command()
@click.option('--domain', '-d', required=True, help='域名')
@click.option('--rr', '-r', help='主机记录过滤')
@click.option('--type', '-t', 'record_type', help='记录类型过滤')
def list_records(domain, rr, record_type):
    """列出DNS记录"""
    
    logger = setup_logger("tencent_dns_list", log_level="INFO", format_type="simple")
    
    try:
        client = TencentDNSClient(logger=logger)
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
