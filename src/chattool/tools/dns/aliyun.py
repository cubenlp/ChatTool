#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import dotenv_values

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_models
from alibabacloud_tea_openapi import models as open_api_models

from chattool.const import CHATTOOL_CONFIG_DIR, CHATTOOL_REPO_DIR
from .base import DNSClient

ALIYUN_ENV_FILE = os.path.join(CHATTOOL_CONFIG_DIR, 'aliyun.env')
REPO_ALIYUN_ENV_FILE = os.path.join(CHATTOOL_REPO_DIR, 'aliyun.env')

class AliyunDNSClient(DNSClient):
    """
    阿里云 DNS 客户端 - 基于官方SDK
    """
    
    def __init__(self, 
                 access_key_id: Optional[str] = None, 
                 access_key_secret: Optional[str] = None,
                 region: str = 'cn-hangzhou',
                 endpoint: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        
        super().__init__(logger=logger)
        
        # 参数验证和环境变量回退
        # 优先读取 CHATTOOL_CONFIG_DIR，其次读取项目根目录
        _env_values = dotenv_values(ALIYUN_ENV_FILE)
        if not _env_values and os.path.exists(REPO_ALIYUN_ENV_FILE):
             _env_values = dotenv_values(REPO_ALIYUN_ENV_FILE)
             
        self.region = region or _env_values.get('ALIBABA_CLOUD_REGION_ID', os.getenv('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou'))
        self.access_key_id = access_key_id or _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        
        if not all([self.access_key_id, self.access_key_secret]):
            raise ValueError("access_key_id 和 access_key_secret 不能为空，请通过参数传入或设置环境变量")
        
        # 初始化官方SDK客户端
        try:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            # 设置端点
            config.endpoint = endpoint or f'alidns.{self.region}.aliyuncs.com'
            
            self.client = Alidns20150109Client(config)
            self.logger.info("阿里云DNS官方SDK客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化阿里云DNS SDK客户端失败: {e}")
            raise

    def describe_domains(self, page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        try:
            request = alidns_models.DescribeDomainsRequest(
                page_number=page_number,
                page_size=min(page_size, 500)
            )
            response = self.client.describe_domains(request)
            
            records = []
            if response.body.domains and response.body.domains.domain:
                for record in response.body.domains.domain:
                    records.append({
                        'DomainName': record.domain_name,
                        'DomainId': record.domain_id,
                        'CreateTime': record.create_time,
                        'Remark': record.remark,
                        'Tags': record.tags.tag
                    })
            return records
        except Exception as e:
            self.logger.error(f"查询域名列表失败: {e}")
            return []

    def describe_domain_records(self, domain_name: str, page_number: int = 1, page_size: int = 20, **kwargs) -> List[Dict[str, Any]]:
        try:
            request = alidns_models.DescribeDomainRecordsRequest(
                domain_name=domain_name,
                page_number=page_number,
                page_size=min(page_size, 500)
            )
            response = self.client.describe_domain_records(request)
            
            records = []
            if response.body.domain_records and response.body.domain_records.record:
                for record in response.body.domain_records.record:
                    records.append({
                        'DomainName': record.domain_name,
                        'RecordId': record.record_id,
                        'RR': record.rr,
                        'Type': record.type,
                        'Value': record.value,
                        'TTL': record.ttl,
                        'Priority': getattr(record, 'priority', None),
                        'Line': getattr(record, 'line', 'default'),
                        'Status': getattr(record, 'status', 'ENABLE'),
                        'Locked': getattr(record, 'locked', False)
                    })
            return records
        except Exception as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []

    def describe_subdomain_records(self, domain_name: str, rr: str) -> List[Dict[str, Any]]:
        """覆盖基类方法，使用专用 API"""
        sub_domain = f"{rr}.{domain_name}"
        try:
            request = alidns_models.DescribeSubDomainRecordsRequest(
                sub_domain=sub_domain
            )
            response = self.client.describe_sub_domain_records(request)
            
            records = []
            if response.body.domain_records and response.body.domain_records.record:
                for record in response.body.domain_records.record:
                    records.append({
                        'DomainName': record.domain_name,
                        'RecordId': record.record_id,
                        'RR': record.rr,
                        'Type': record.type,
                        'Value': record.value,
                        'TTL': record.ttl,
                        'Status': getattr(record, 'status', 'ENABLE'),
                    })
            return records
        except Exception as e:
            self.logger.error(f"查询子域名解析记录失败: {e}")
            return []

    def add_domain_record(self, domain_name: str, rr: str, type_: str, value: str, ttl: int = 600, **kwargs) -> Optional[str]:
        try:
            request = alidns_models.AddDomainRecordRequest(
                domain_name=domain_name,
                rr=rr,
                type=type_,
                value=value,
                ttl=ttl,
                line=kwargs.get('line', 'default')
            )
            
            if type_.upper() == 'MX' and kwargs.get('priority') is not None:
                request.priority = kwargs.get('priority')
            
            response = self.client.add_domain_record(request)
            return response.body.record_id
        except Exception as e:
            self.logger.error(f"创建DNS记录失败: {e}")
            return None

    def update_domain_record(self, record_id: str, rr: str, type_: str, value: str, domain_name: str = None, ttl: int = 600, **kwargs) -> bool:
        try:
            request = alidns_models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=type_,
                value=value,
                ttl=ttl,
                line=kwargs.get('line', 'default')
            )
            
            if type_.upper() == 'MX' and kwargs.get('priority') is not None:
                request.priority = kwargs.get('priority')
            
            self.client.update_domain_record(request)
            return True
        except Exception as e:
            self.logger.error(f"更新DNS记录失败: {e}")
            return False

    def delete_domain_record(self, record_id: str, domain_name: str = None) -> bool:
        try:
            request = alidns_models.DeleteDomainRecordRequest(
                record_id=record_id
            )
            self.client.delete_domain_record(request)
            return True
        except Exception as e:
            self.logger.error(f"删除DNS记录失败: {e}")
            return False
