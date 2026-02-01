import os
from enum import Enum
from typing import Union, Optional
from .aliyun import AliyunDNSClient
from .tencent import TencentDNSClient

class DNSClientType(Enum):
    ALIYUN = 'aliyun'
    TENCENT = 'tencent'

def create_dns_client(dns_type: Optional[Union[DNSClientType, str]] = None, **kwargs):
    """
    创建DNS客户端工厂方法
    
    Args:
        dns_type: DNS服务商类型 ('aliyun', 'tencent')。如果未提供，尝试从环境变量 DEFAULT_DNS_PROVIDER 获取，默认为 'aliyun'
        **kwargs: 传递给客户端的参数
    """
    if dns_type is None:
        dns_type = os.environ.get('DEFAULT_DNS_PROVIDER', 'aliyun')
        
    if isinstance(dns_type, DNSClientType):
        dns_type = dns_type.value
        
    if dns_type == 'aliyun':
        return AliyunDNSClient(**kwargs)
    elif dns_type == 'tencent':
        return TencentDNSClient(**kwargs)
    else:
        raise ValueError(f"Unsupported DNS type: {dns_type}")
