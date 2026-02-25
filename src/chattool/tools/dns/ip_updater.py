#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IP监控和DNS自动更新脚本

用于监控本机公网IP地址变化，当检测到IP变化时自动更新腾讯云DNSPod解析记录。
适用于动态IP环境下的域名解析自动维护。
"""

import asyncio
import aiohttp
import ipaddress
from typing import Optional, Dict, Any, Union

from chattool.utils import setup_logger
from .utils import create_dns_client, DNSClientType

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
                log_file: Optional[str] = None,
                dns_type: Union[DNSClientType, str]='aliyun',
                ip_type: str = 'public',  # 'public' or 'local'
                local_ip_cidr: Optional[str] = None, # e.g. '192.168.0.0/16'
                **dns_client_kwargs
        ):
        """初始化更新器
        
        Args:
            domain_name: 域名
            rr: 子域名记录
            record_type: DNS记录类型，默认为A记录，支持A、CNAME、MX等
            dns_ttl: TTL值
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            logger: 日志记录器
            log_file: 日志文件路径 (如果未提供 logger 且需要文件日志)
            dns_type: DNS客户端类型
            ip_type: IP类型，'public' 或 'local'
            local_ip_cidr: 局域网IP过滤网段，仅当 ip_type='local' 时有效
            dns_client_kwargs: DNS客户端初始化参数
        """
        self.domain_name = domain_name
        self.rr = rr
        self.record_type = record_type
        self.dns_ttl = dns_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or setup_logger(__name__, log_file=log_file)
        self.ip_type = ip_type
        self.local_ip_cidr = local_ip_cidr
        
        # 初始化DNS客户端
        try:
            self.dns_client = create_dns_client(dns_type, logger=self.logger, **dns_client_kwargs)
            client_type_name = dns_type.value if hasattr(dns_type, 'value') else str(dns_type)
            self.logger.info(f"{client_type_name} DNS客户端初始化成功")
        except Exception as e:
            client_type_name = dns_type.value if hasattr(dns_type, 'value') else str(dns_type)
            self.logger.error(f"{client_type_name} DNS客户端初始化失败: {e}")
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
    
    async def get_ip(self) -> Optional[str]:
        """
        获取当前设备的公网或局域网IP
        
        Returns:
            IP地址字符串，获取失败返回None
        """
        if self.ip_type == 'public':
            return await self.get_public_ip()
        elif self.ip_type == 'local':
            return self.get_local_ip()
        else:
            self.logger.error(f"不支持的IP类型: {self.ip_type}")
            return None

    def get_local_ip(self) -> Optional[str]:
        """获取局域网IP地址"""
        try:
            # 获取所有网络接口
            import netifaces
            interfaces = netifaces.interfaces()
            candidates = []

            for iface in interfaces:
                # 排除 lo 接口
                if iface == 'lo':
                    continue
                    
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info['addr']
                        # 排除回环地址
                        if ip.startswith('127.'):
                            continue
                        
                        # 如果指定了网段，进行过滤
                        if self.local_ip_cidr:
                            try:
                                network = ipaddress.ip_network(self.local_ip_cidr, strict=False)
                                if ipaddress.ip_address(ip) in network:
                                    candidates.append(ip)
                            except ValueError:
                                self.logger.warning(f"无效的网段格式: {self.local_ip_cidr}")
                                continue
                        else:
                            # 如果没有指定网段，优先选择常见的局域网网段
                            # 192.168.x.x, 10.x.x.x, 172.16.x.x - 172.31.x.x
                            # 以及常见的 VPN/Tailscale 网段如 100.x.x.x
                            if ip.startswith(('192.168.', '10.', '172.', '100.')):
                                candidates.append(ip)
            
            if not candidates:
                self.logger.warning("未找到合适的局域网IP")
                return None
            
            if len(candidates) > 1:
                self.logger.info(f"找到多个局域网IP: {candidates}，将使用第一个")
            
            return candidates[0]
            
        except Exception as e:
            self.logger.error(f"获取局域网IP失败: {e}")
            return None

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
        """
        更新DNS记录为新的IP
        
        Args:
            new_ip: 新的IP地址
            
        Returns:
            是否更新成功
        """
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
        """
        检查当前IP与DNS记录是否一致，不一致则更新
        
        Returns:
            操作是否成功（IP无变化也视为成功）
        """
        # 获取当前IP
        current_ip = await self.get_ip()
        if not current_ip:
            self.logger.error("无法获取当前IP")
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
        """
        持续运行监控循环
        
        Args:
            interval: 检查间隔（秒）
        """
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
        """
        运行一次检查和更新
        
        Returns:
            操作是否成功
        """
        self.logger.info(f"执行一次IP检查和DNS更新: {self.rr}.{self.domain_name}")
        return await self.check_and_update()
