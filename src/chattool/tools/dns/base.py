import logging
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class DNSClient(ABC):
    """DNS 客户端抽象基类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None, **kwargs):
        self.logger = logger or logging.getLogger(__name__)

    # --- 基础 CRUD 接口 (必须实现) ---

    @abstractmethod
    def describe_domains(self, page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        获取域名列表
        返回格式: [{'DomainName': 'example.com', 'DomainId': '...', ...}, ...]
        """
        pass

    @abstractmethod
    def describe_domain_records(self, domain_name: str, page_number: int = 1, page_size: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """
        获取指定域名的解析记录列表
        返回格式: [{'RecordId': '...', 'RR': 'www', 'Type': 'A', 'Value': '1.1.1.1', ...}, ...]
        """
        pass

    @abstractmethod
    def add_domain_record(self, domain_name: str, rr: str, type_: str, value: str, ttl: int = 600, **kwargs) -> Optional[str]:
        """
        添加解析记录
        Returns: record_id (str) or None
        """
        pass

    @abstractmethod
    def update_domain_record(self, record_id: str, rr: str, type_: str, value: str, domain_name: str = None, ttl: int = 600, **kwargs) -> bool:
        """
        更新解析记录
        注意: domain_name 参数在腾讯云中是必须的，在阿里云中可选
        """
        pass

    @abstractmethod
    def delete_domain_record(self, record_id: str, domain_name: str = None) -> bool:
        """
        删除解析记录
        注意: domain_name 参数在腾讯云中是必须的
        """
        pass

    # --- 高级通用接口 (提供默认实现，子类可覆盖) ---

    def describe_subdomain_records(self, domain_name: str, rr: str) -> List[Dict[str, Any]]:
        """
        获取特定子域名的记录
        默认实现：获取所有记录后在内存中过滤
        子类应该尽可能覆盖此方法以使用服务端过滤
        """
        try:
            # 获取所有记录 (简化版，未处理分页)
            # 实际上这可能效率低下，建议子类实现服务端过滤
            records = self.describe_domain_records(domain_name, page_size=500)
            return [r for r in records if r.get('RR') == rr]
        except Exception as e:
            self.logger.error(f"获取子域名记录失败: {e}")
            return []

    def set_record_value(self, domain_name: str, rr: str, type_: str, value: str, ttl: int = 600, **kwargs) -> bool:
        """
        幂等设置记录值：
        1. 记录不存在 -> 创建
        2. 记录存在 -> 更新
        3. 存在多条 -> 报错或清理
        """
        try:
            # 1. 查找现有记录
            records = self.describe_subdomain_records(domain_name, rr)
            # 过滤类型
            records = [r for r in records if r.get('Type') == type_]
            
            if not records:
                # 不存在，创建新记录
                self.logger.info(f"创建新记录: {rr}.{domain_name} {type_} {value}")
                record_id = self.add_domain_record(domain_name, rr, type_, value, ttl, **kwargs)
                return record_id is not None
            
            if len(records) > 1:
                self.logger.warning(f"子域名 {rr}.{domain_name} 存在多个 {type_} 记录，将更新第一个")
                # 可选：删除多余的？暂时只更新第一个
            
            record = records[0]
            if record.get('Value') == value and str(record.get('TTL')) == str(ttl):
                 self.logger.info(f"记录已存在且一致，无需更新: {rr}.{domain_name} {type_} {value}")
                 return True

            # 更新现有记录
            self.logger.info(f"更新现有记录: {record.get('RecordId')} -> {value}")
            return self.update_domain_record(
                record_id=record.get('RecordId'),
                rr=rr,
                type_=type_,
                value=value,
                domain_name=domain_name,
                ttl=ttl,
                **kwargs
            )
                
        except Exception as e:
            self.logger.error(f"设置DNS记录失败: {e}")
            return False

    def delete_subdomain_records(self, domain_name: str, rr: str, type_: str = None) -> bool:
        """删除子域名的所有解析记录"""
        try:
            records = self.describe_subdomain_records(domain_name, rr)
            if type_:
                records = [r for r in records if r.get('Type') == type_]
            
            if not records:
                return True
            
            success = True
            for record in records:
                self.logger.info(f"删除记录: {record.get('RecordId')} ({rr}.{domain_name})")
                if not self.delete_domain_record(record.get('RecordId'), domain_name):
                    success = False
            return success
        except Exception as e:
            self.logger.error(f"删除子域名记录失败: {e}")
            return False

    def delete_record_value(self, domain_name: str, rr: str, type_: str, value: Optional[str] = None) -> bool:
        """
        删除指定值的记录
        
        Args:
            domain_name: 域名
            rr: 主机记录
            type_: 记录类型
            value: 记录值 (可选，如果未提供则删除所有匹配 rr 和 type 的记录)
            
        Returns:
            是否成功
        """
        try:
            records = self.describe_subdomain_records(domain_name, rr)
            
            deleted_count = 0
            for record in records:
                if record['Type'] != type_:
                    continue
                    
                if value is None or record['Value'] == value:
                    if self.delete_domain_record(record['RecordId'], domain_name=domain_name):
                        deleted_count += 1
            
            return deleted_count > 0
        except Exception as e:
            self.logger.error(f"批量删除DNS记录失败: {e}")
            return False

    async def get_public_ip(self, timeout: int = 10) -> Optional[str]:
        """获取当前公网IP地址 (异步工具方法)"""
        ip_check_urls = [
            "https://ipv4.icanhazip.com",
            "https://api.ipify.org",
            "https://ipinfo.io/ip",
            "https://checkip.amazonaws.com",
            "https://ident.me",
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            for url in ip_check_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            ip = (await response.text()).strip()
                            # 简单验证 IP 格式
                            if len(ip.split('.')) == 4:
                                return ip
                except Exception:
                    continue
        return None
