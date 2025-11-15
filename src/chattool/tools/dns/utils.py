from enum import Enum
from typing import Union
from ..aliyun_dns.client import AliyunDNSClient
from ..tencent_dns import TencentDNSClient

class DNSClientType(Enum):
    ALIYUN = 'aliyun'
    TENCENT = 'tencent'

def create_dns_client(dns_type: Union[DNSClientType, str]='aliyun', **kwargs):
    if isinstance(dns_type, DNSClientType):
        dns_type = dns_type.value
    if dns_type == 'aliyun':
        return AliyunDNSClient(**kwargs)
    elif dns_type == 'tencent':
        return TencentDNSClient(**kwargs)
    else:
        raise ValueError(f"Unsupported DNS type: {dns_type}")
