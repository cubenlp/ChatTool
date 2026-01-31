#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL证书自动更新 CLI
"""

import click
import asyncio
from chattool.utils import setup_logger
from chattool.tools.dns.cert_updater import SSLCertUpdater, CERT_DIR, PRIVATE_KEY_DIR, LOG_FILE

# 命令行入口
@click.command()
@click.option('--domains', '-d', multiple=True, required=True, help='域名列表，可以指定多个')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt账户邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录，默认 {CERT_DIR}')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录，默认 {PRIVATE_KEY_DIR}')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
@click.option('--log-file', default=LOG_FILE, help=f'日志文件路径，默认 {LOG_FILE}')
def main(domains, email, cert_dir, private_key_dir, staging, log_file):
    """SSL证书自动更新工具
    
    使用Let's Encrypt和阿里云DNS自动申请和更新SSL证书。
    
    示例:
    
    chattool script cert-updater -d example.com -d www.example.com -e admin@example.com
    chattool script cert-updater -d example.com -d api.example.com -d www.example.com -e admin@example.com --staging
    """
    logger = setup_logger('ssl_cert_updater', log_file)
    
    click.echo(f"启动SSL证书更新器...")
    click.echo(f"域名: {', '.join(domains)}")
    click.echo(f"邮箱: {email}")
    click.echo(f"证书目录: {cert_dir}")
    click.echo(f"私钥目录: {private_key_dir}")
    click.echo(f"环境: {'测试' if staging else '生产'}")
    click.echo("")
    
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
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
