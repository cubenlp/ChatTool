#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import List, Dict, Optional, Any

try:
    from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
    from alibabacloud_alidns20150109 import models as alidns_models
    from alibabacloud_tea_openapi import models as open_api_models
    ALIYUN_AVAILABLE = True
except ImportError:
    ALIYUN_AVAILABLE = False
    Alidns20150109Client = None
    alidns_models = None
    open_api_models = None

from chattool.config import AliyunConfig

from .base import DNSClient

class AliyunDNSClient(DNSClient):
    """
    阿里云 DNS 客户端 - 基于官方SDK
    """
    def __init__(self, 
                 access_key_id: Optional[str] = None, 
                 access_key_secret: Optional[str] = None,
                 region: str = None,
                 endpoint: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        
        if not ALIYUN_AVAILABLE:
            raise ImportError("阿里云SDK未安装，请安装 chattool[tools] 或 alibabacloud 相关包")

        super().__init__(logger=logger)
        
        # 参数验证和环境变量回退
        self.region = region or AliyunConfig.ALIBABA_CLOUD_REGION_ID.value or 'cn-hangzhou'
        self.access_key_id = access_key_id or AliyunConfig.ALIBABA_CLOUD_ACCESS_KEY_ID.value
        self.access_key_secret = access_key_secret or AliyunConfig.ALIBABA_CLOUD_ACCESS_KEY_SECRET.value
        
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
        """
        获取域名列表
        
        Args:
            page_number: 页码，默认1
            page_size: 每页数量，默认20
            
        Returns:
            域名列表，每个元素包含 DomainName, DomainId 等信息
        """
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
        """
        获取域名解析记录列表
        
        Args:
            domain_name: 域名名称
            page_number: 页码，默认1
            page_size: 每页数量，默认20
            **kwargs: 可选参数
                subdomain: 主机记录关键字
                record_type: 记录类型关键字
            
        Returns:
            解析记录列表
        """
        # Handle subdomain/record_type filters from kwargs
        subdomain = kwargs.get('subdomain')
        record_type = kwargs.get('record_type')
        
        # Let's keep using DescribeDomainRecords but add filters if SDK supports
        try:
            request = alidns_models.DescribeDomainRecordsRequest(
                domain_name=domain_name,
                page_number=page_number,
                page_size=min(page_size, 500)
            )
            
            # Add filters
            if subdomain:
                request.rrkey_word = subdomain
                request.search_mode = "EXACT" # If supported? Or just filter locally.
                # Aliyun SDK RRKeyWord matches partial? 
                # Better use DescribeSubDomainRecords if subdomain is set.
                return self.describe_subdomain_records(domain_name, subdomain)

            if record_type:
                request.type_key_word = record_type

            response = self.client.describe_domain_records(request)
            
            records = []
            if response.body.domain_records and response.body.domain_records.record:
                for record in response.body.domain_records.record:
                    # Local filter if needed (e.g. if API doesn't support exact match for Type)
                    if record_type and record.type != record_type:
                        continue
                        
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
        """
        添加域名解析记录
        
        Args:
            domain_name: 域名名称
            rr: 主机记录
            type_: 记录类型 (A, CNAME, TXT, MX 等)
            value: 记录值
            ttl: TTL值
            **kwargs: 可选参数 (priority, line等)
            
        Returns:
            记录ID，失败返回None
        """
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
        """
        更新域名解析记录
        
        Args:
            record_id: 记录ID
            rr: 主机记录
            type_: 记录类型
            value: 记录值
            domain_name: 域名名称 (阿里云API不需要，但为了统一接口保留)
            ttl: TTL值
            **kwargs: 可选参数
            
        Returns:
            是否成功
        """
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
        """
        删除域名解析记录
        
        Args:
            record_id: 记录ID
            domain_name: 域名名称 (可选)
            
        Returns:
            是否成功
        """
        try:
            request = alidns_models.DeleteDomainRecordRequest(
                record_id=record_id
            )
            self.client.delete_domain_record(request)
            return True
        except Exception as e:
            self.logger.error(f"删除DNS记录失败: {e}")
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
