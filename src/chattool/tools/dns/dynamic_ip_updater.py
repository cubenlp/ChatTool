#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新脚本

用于监控本机公网IP地址变化，当检测到IP变化时自动更新腾讯云DNSPod解析记录。
适用于动态IP环境下的域名解析自动维护。
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Union
from chattool.utils import setup_logger
from .utils import create_dns_client, DNSClientType

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
                dns_ttl: int = 600,
                max_retries: int = 3,
                retry_delay: int = 5,
                logger=None,
                dns_type: Union[DNSClientType, str]='aliyun',
                **dns_client_kwargs
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
            dns_type: DNS客户端类型
            dns_client_kwargs: DNS客户端初始化参数
        """
        self.domain_name = domain_name
        self.rr = rr
        self.record_type = record_type
        self.dns_ttl = dns_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or setup_logger(__name__)
        
        # 初始化DNS客户端
        try:
            self.dns_client = create_dns_client(dns_type, logger=self.logger, **dns_client_kwargs)
            self.logger.info(f"{dns_type.value} DNS客户端初始化成功")
        except Exception as e:
            self.logger.error(f"{dns_type.value} DNS客户端初始化失败: {e}")
            raise
        
        # IP检查服务列表
        self.ip_check_urls = [
            "https://ipv4.icanhazip.com",
            "https://api.ipify.org",
            "https://ipinfo.io/ip",
            "https://checkip.amazonaws.com",
            "https://ident.me",
            "https://v4.ident.me",
        ]
        
        self.current_ip = None
    
    async def get_public_ip(self) -> Optional[str]:
        """获取当前公网IP地址"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=IP_CHECK_TIMEOUT)) as session:
            for url in self.ip_check_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            ip = (await response.text()).strip()
                            if self._is_valid_ip(ip):
                                self.logger.debug(f"从 {url} 获取到IP: {ip}")
                                return ip
                except Exception as e:
                    self.logger.warning(f"从 {url} 获取IP失败: {e}")
                    continue
        
        self.logger.error("所有IP检查服务都失败")
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except ValueError:
            return False
    
    def get_current_dns_record(self) -> Optional[Dict[str, Any]]:
        """获取当前的DNS记录"""
        try:
            records = self.dns_client.describe_domain_records(
                domain_name=self.domain_name,
                subdomain=self.rr,
                record_type=self.record_type
            )
            
            if not records:
                self.logger.info(f"未找到 {self.rr}.{self.domain_name} 的 {self.record_type} 记录")
                return None
            
            if len(records) > 1:
                self.logger.warning(f"找到多个 {self.rr}.{self.domain_name} 的 {self.record_type} 记录")
                # 返回第一个记录
                return records[0]
            
            return records[0]
            
        except Exception as e:
            self.logger.error(f"获取DNS记录失败: {e}")
            return None
    
    def update_dns_record(self, new_ip: str) -> bool:
        """更新DNS记录"""
        try:
            # 使用set_record_value方法，自动处理创建或更新
            success = self.dns_client.set_record_value(
                domain_name=self.domain_name,
                rr=self.rr,
                type_=self.record_type,
                value=new_ip,
                ttl=self.dns_ttl
            )
            
            if success:
                self.logger.info(f"DNS记录更新成功: {self.rr}.{self.domain_name} {self.record_type} {new_ip}")
                return True
            else:
                self.logger.error("DNS记录更新失败")
                return False
                
        except Exception as e:
            self.logger.error(f"更新DNS记录时发生异常: {e}")
            return False
    
    async def check_and_update(self) -> bool:
        """检查IP并更新DNS记录"""
        # 获取当前公网IP
        current_ip = await self.get_public_ip()
        if not current_ip:
            self.logger.error("无法获取当前公网IP")
            return False
        
        # 检查IP是否有变化
        if current_ip == self.current_ip:
            self.logger.debug(f"IP没有变化: {current_ip}")
            return True
        
        self.logger.info(f"检测到IP变化: {self.current_ip} -> {current_ip}")
        
        # 获取当前DNS记录
        dns_record = self.get_current_dns_record()
        if dns_record and dns_record['Value'] == current_ip:
            self.logger.info("DNS记录已经是最新IP，无需更新")
            self.current_ip = current_ip
            return True
        
        # 更新DNS记录
        for attempt in range(self.max_retries):
            try:
                if self.update_dns_record(current_ip):
                    self.current_ip = current_ip
                    self.logger.info(f"IP更新成功: {self.rr}.{self.domain_name} -> {current_ip}")
                    return True
                else:
                    self.logger.warning(f"第 {attempt + 1} 次更新尝试失败")
                    
            except Exception as e:
                self.logger.error(f"第 {attempt + 1} 次更新尝试发生异常: {e}")
            
            if attempt < self.max_retries - 1:
                self.logger.info(f"等待 {self.retry_delay} 秒后重试...")
                await asyncio.sleep(self.retry_delay)
        
        self.logger.error(f"DNS记录更新失败，已重试 {self.max_retries} 次")
        return False
    
    async def run_continuous(self, interval: int = IP_CHECK_INTERVAL):
        """持续运行监控"""
        self.logger.info(f"开始持续监控 {self.rr}.{self.domain_name} 的IP变化...")
        self.logger.info(f"检查间隔: {interval} 秒")
        
        # 初始检查
        await self.check_and_update()
        
        # 持续监控
        while True:
            try:
                await asyncio.sleep(interval)
                await self.check_and_update()
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，停止监控")
                break
            except Exception as e:
                self.logger.error(f"监控过程中发生异常: {e}")
                await asyncio.sleep(interval)
                continue
    
    async def run_once(self) -> bool:
        """运行一次检查和更新"""
        self.logger.info(f"执行一次IP检查和DNS更新: {self.rr}.{self.domain_name}")
        return await self.check_and_update()
