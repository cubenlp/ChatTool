#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DNS 工具包

提供阿里云域名解析服务(DNS)的完整 Python 客户端实现，支持域名解析记录的 CRUD 操作。

主要功能:
- 查看域名解析记录 (describe_domain_records)
- 创建域名解析记录 (add_domain_record)  
- 修改域名解析记录 (update_domain_record)
- 删除域名解析记录 (delete_domain_record)
- 支持同步和异步调用方式
- 完善的错误处理和日志记录

使用示例:
    >>> from chattool.tools import AliyunDNSClient
    >>> client = AliyunDNSClient()
    >>> records = client.describe_domain_records("example.com")
    >>> for record in records:
    ...     print(f"{record['RR']}.{record['DomainName']} -> {record['Value']}")

环境变量配置:
    ALIBABA_CLOUD_ACCESS_KEY_ID: 阿里云 Access Key ID
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: 阿里云 Access Key Secret  
    ALIBABA_CLOUD_REGION_ID: 区域 ID（可选，默认 cn-hangzhou）
"""

# 主要客户端类
from .client import AliyunDNSClient

# 配置管理类
from .config import (
    AliyunDNSConfig,
    DNSRecordType, 
    DNSLineType,
    AliyunRegion
)

# 导出的公共接口
__all__ = [
    # 主要客户端
    'AliyunDNSClient',
    'create_dns_client',
    
    # 配置管理
    'AliyunDNSConfig', 
    'create_config_from_env',
    'create_config_for_region',
    
    # 常量类
    'DNSRecordType',
    'DNSLineType', 
    'AliyunRegion',
]