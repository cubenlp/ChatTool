#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新脚本

用于监控本机公网IP地址变化，当检测到IP变化时自动更新阿里云DNS解析记录。
适用于动态IP环境下的域名解析自动维护。
"""

import click
import asyncio
from httpx import AsyncClient
from typing import Optional, Dict, Any
from batch_executor import setup_logger
from .client import AliyunDNSClient

# 域名配置
LOG_FILE = "dynamic_ip_updater.log"           # 日志文件路径

# IP检查服务列表（故障切换用）
IP_CHECK_TIMEOUT = 10                    # IP检查超时时间（秒）
IP_CHECK_INTERVAL = 120                   # IP检查间隔（秒）

class DynamicIPUpdater:
    """动态IP监控和DNS更新器"""
    
    def __init__(self,
                domain_name: str, 
                rr: str, 
                record_type: str = "A",
                dns_ttl: int=600,
                max_retries: int=3,
                retry_delay: int=5,
                logger=None
        ):
        """初始化更新器
        
        Args:
            domain_name: 域名
            rr: 子域名记录
            record_type: DNS记录类型，默认为A记录
            dns_ttl: TTL值
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            logger: 日志记录器
        """
        self.domain_name = domain_name
        self.rr = rr
        self.record_type = record_type
        self.dns_ttl = dns_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.logger = logger or setup_logger(__name__, log_file=LOG_FILE)
        self.dns_record = None
        self.current_ip = None
        self.last_updated_ip = None
        
        # 初始化DNS客户端
        self.dns_client = AliyunDNSClient()
        
        self.logger.info(f"动态IP更新器 -- 域名: {self.domain_name}, 子域名: {self.rr}, 记录类型: {self.record_type}")

    async def get_current_ip(self) -> Optional[str]:
        """
        获取当前公网IP地址
        
        Returns:
            当前IP地址，获取失败时返回None
        """
        # IP检查服务列表（故障切换用）
        ip_services = [
            "https://ipinfo.io/ip",
            "https://checkip.amazonaws.com"
        ]
        
        async with AsyncClient() as client:
            for service in ip_services:
                try:
                    response = await client.get(service, timeout=IP_CHECK_TIMEOUT)
                    response.raise_for_status()
                    ip = response.text.strip()
                    if self.is_valid_ip(ip):
                        self.logger.debug(f"从 {service} 获取到IP地址: {ip}")
                        return ip
                    else:
                        self.logger.warning(f"从 {service} 获取的IP格式无效: {ip}")
                except Exception as e:
                    self.logger.warning(f"从 {service} 获取IP时出错: {e}")
                    continue
        
        self.logger.error("所有IP检查服务都失败了")
        return None
    
    def is_valid_ip(self, ip: str) -> bool:
        """
        验证IP地址格式
        
        Args:
            ip: IP地址字符串
            
        Returns:
            IP是否有效
        """
        try:
            parts = ip.split('.')
            return (len(parts) == 4 and 
                   all(0 <= int(part) <= 255 for part in parts))
        except (ValueError, AttributeError):
            return False
    
    def get_current_dns_record(self) -> Optional[Dict[str, Any]]:
        """
        获取当前DNS记录
        
        Returns:
            当前DNS记录，如果不存在返回None
        """
        try:
            records = self.dns_client.describe_subdomain_records(
                f"{self.rr}.{self.domain_name}"
            )
            if len(records) == 1:
                return records[0]
            elif len(records) > 1:
                self.logger.warning(f"发现多个 {self.record_type} 记录，使用第一个")
                return records[0]
            else:
                self.logger.info(f"未找到 {self.rr}.{self.domain_name} 的 {self.record_type} 记录")
                return None
                
        except Exception as e:
            self.logger.error(f"获取DNS记录失败: {e}")
            return None
    
    async def check_and_update_ip(self) -> bool:
        """
        检查IP变化并更新DNS记录
        
        Returns:
            是否有更新操作
        """
        # 获取当前IP
        current_ip = await self.get_current_ip()
        if not current_ip:
            self.logger.error("无法获取当前IP地址")
            return False
        
        self.current_ip = current_ip
        
        # 检查IP是否发生变化
        if self.last_updated_ip == current_ip:
            self.logger.debug(f"IP地址未发生变化: {current_ip}")
            return False
        
        self.logger.info(f"检测到IP地址变化: {self.last_updated_ip} -> {current_ip}")
        
        # 更新DNS记录
        for attempt in range(self.max_retries):
            if self.dns_client.set_record_value(self.domain_name, self.rr, self.record_type, current_ip, self.dns_ttl):
                # 验证DNS记录是否更新成功
                await asyncio.sleep(2)  # 等待DNS记录生效
                updated_record = self.get_current_dns_record()
                
                if updated_record and updated_record['Value'] == current_ip:
                    self.last_updated_ip = current_ip
                    self.logger.info(f"DNS记录验证成功，IP已更新为: {current_ip}")
                    return True
                else:
                    self.logger.warning(f"DNS记录验证失败，尝试重新更新 (第{attempt + 1}次)")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        self.logger.error(f"DNS记录更新失败，已重试 {self.max_retries} 次")
        return False
    
    async def run_once(self) -> bool:
        """
        执行一次IP检查和更新
        
        Returns:
            是否有更新操作
        """
        try:
            return await self.check_and_update_ip()
        except Exception as e:
            self.logger.error(f"运行时发生异常: {e}")
            return False
    
    async def run(self, check_interval: int = None) -> None:
        """
        持续运行IP监控和DNS更新
        
        Args:
            check_interval: 检查间隔（秒），默认使用全局配置
        """
        interval = check_interval or IP_CHECK_INTERVAL
        self.logger.info(f"开始持续监控，检查间隔: {interval} 秒")
        
        # 初始化时获取当前DNS记录的IP
        try:
            current_record = self.get_current_dns_record()
            if current_record:
                self.last_updated_ip = current_record['Value']
                self.logger.info(f"当前DNS记录IP: {self.last_updated_ip}")
        except Exception as e:
            self.logger.warning(f"获取初始DNS记录失败: {e}")
        
        # 主循环
        while True:
            try:
                await self.run_once()
                await asyncio.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，停止监控")
                break
            except Exception as e:
                self.logger.error(f"主循环发生异常: {e}")
                await asyncio.sleep(interval)
    
    def run_sync(self, check_interval: int = None) -> None:
        """
        同步方式运行（阻塞）
        
        Args:
            check_interval: 检查间隔（秒），默认使用全局配置
        """
        try:
            asyncio.run(self.run(check_interval))
        except KeyboardInterrupt:
            self.logger.info("程序被用户中断")
        except Exception as e:
            self.logger.error(f"程序运行异常: {e}")

# 命令行入口
@click.command()
@click.argument('domain_name')
@click.argument('rr')
@click.option('--record-type', default='A', help='DNS记录类型，默认为A')
@click.option('--ttl', type=int, default=600, help='TTL值，默认300秒')
@click.option('--interval', type=int, default=IP_CHECK_INTERVAL, help=f'检查间隔，默认{IP_CHECK_INTERVAL}秒')
@click.option('--max-retries', type=int, default=3, help='最大重试次数，默认3次')
@click.option('--retry-delay', type=int, default=5, help='重试延迟，默认5秒')
@click.option('--log-file', default=LOG_FILE, help='日志文件路径，默认 dynamic_ip_updater.log')
def main(domain_name, rr, record_type, ttl, interval, max_retries, retry_delay, log_file):
    """动态IP监控和DNS自动更新工具
    
    监控本机公网IP地址变化，当检测到IP变化时自动更新阿里云DNS解析记录。
    
    示例:
    \b
    chattool.aliyun-dns-updater example.com home
    chattool.aliyun-dns-updater example.com www --ttl 600 --interval 60
    """
    logger = setup_logger('dynamic_ip_updater', log_file)
    click.echo(f"启动动态IP更新器...")
    click.echo(f"域名: {domain_name}")
    click.echo(f"子域名: {rr}")
    click.echo(f"记录类型: {record_type}")
    click.echo(f"TTL: {ttl}秒")
    click.echo(f"检查间隔: {interval}秒")
    click.echo("按 Ctrl+C 停止监控\n")
    
    updater = DynamicIPUpdater(
        domain_name=domain_name,
        rr=rr,
        record_type=record_type,
        dns_ttl=ttl,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger,
    )
    try:
        updater.run_sync(interval)
    except KeyboardInterrupt:
        click.echo("\n程序已停止")
    except Exception as e:
        click.echo(f"程序运行出错: {e}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    main()