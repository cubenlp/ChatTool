from enum import Enum
from typing import Union

from .base import DNSClient
from .aliyun import AliyunDNSClient
from .tencent import TencentDNSClient
from .ip_updater import DynamicIPUpdater

class DNSClientType(Enum):
    ALIYUN = 'aliyun'
    TENCENT = 'tencent'

def create_dns_client(dns_type: Union[DNSClientType, str]='aliyun', **kwargs) -> DNSClient:
    """
    创建 DNS 客户端工厂函数
    
    Args:
        dns_type: DNS 类型 ('aliyun' 或 'tencent')
        **kwargs: 传递给客户端构造函数的参数
    """
    if isinstance(dns_type, DNSClientType):
        dns_type = dns_type.value
    
    if dns_type == 'aliyun':
        return AliyunDNSClient(**kwargs)
    elif dns_type == 'tencent':
        return TencentDNSClient(**kwargs)
    else:
        raise ValueError(f"Unsupported DNS type: {dns_type}")

__all__ = [
    'DNSClient',
    'AliyunDNSClient',
    'TencentDNSClient',
    'DNSClientType',
    'create_dns_client',
    'DynamicIPUpdater',
]
