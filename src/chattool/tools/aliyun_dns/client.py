#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DNS 客户端 - 基于官方SDK

基于阿里云官方 SDK 实现域名解析记录的 CRUD 操作，包括：
- 查看解析记录 (DescribeDomainRecords)
- 创建解析记录 (AddDomainRecord)
- 修改解析记录 (UpdateDomainRecord)  
- 删除解析记录 (DeleteDomainRecord)
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import dotenv_values

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_models
from alibabacloud_tea_openapi import models as open_api_models

from chattool.utils import setup_logger
from chattool.const import CHATTOOL_CONFIG_DIR

ALIYUN_ENV_FILE = os.path.join(CHATTOOL_CONFIG_DIR, 'aliyun.env')

class AliyunDNSClient:
    """
    阿里云 DNS 客户端 - 基于官方SDK
    
    提供域名解析记录的完整 CRUD 操作功能。
    """
    
    def __init__(self, 
                 access_key_id: Optional[str] = None, 
                 access_key_secret: Optional[str] = None,
                 region:str='cn-hangzhou',
                 endpoint: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化阿里云 DNS 客户端
        
        Args:
            access_key_id: 阿里云 Access Key ID，如果为空，则从 aliyun.env 文件或环境变量获取
            access_key_secret: 阿里云 Access Key Secret，如果为空，则从 aliyun.env 文件或环境变量获取
            region: API 区域，默认为 cn-hangzhou
            endpoint: API 端点，默认为 alidns.cn-hangzhou.aliyuncs.com
            logger: 日志记录器，如果为空则创建默认记录器
        
        Raises:
            ValueError: 当认证信息不完整时抛出异常
        """
        # 参数验证和环境变量回退
        
        _env_values = dotenv_values(ALIYUN_ENV_FILE)        
        self.region = region or _env_values.get('ALIBABA_CLOUD_REGION_ID', os.getenv('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou'))
        self.access_key_id = access_key_id or _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        
        if not all([self.access_key_id, self.access_key_secret]):
            raise ValueError("access_key_id 和 access_key_secret 不能为空，请通过参数传入或设置环境变量")
        
        # 设置日志记录器
        self.logger = logger or setup_logger(__name__)
        
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
        查看域名列表 (Read)
        
        Args:
            page_number: 页码，默认为 1
            page_size: 每页记录数，默认为 20，最大值 500
            
        Returns:
            域名列表
            
        Example:
            >>> client = AliyunDNSClient()
            >>> domains = client.describe_domains()
            >>> for domain in domains:
            ...     print(f"{domain['DomainName']} ({domain['DomainId']})")
        """
        try:
            self.logger.info(f"查询域名列表")

            # 构造请求
            request = alidns_models.DescribeDomainsRequest(
                page_number=page_number,
                page_size=min(page_size, 500)  # 限制最大页面大小
            )
            
            # 发送请求
            response = self.client.describe_domains(request)
            
            # 提取记录列表
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
            self.logger.info(f"成功获取 {len(records)} 条域名列表")
            return records
            
        except Exception as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []
    
    def describe_domain_records(self, domain_name: str, 
                              page_number: int = 1,
                              page_size: int = 20) -> List[Dict[str, Any]]:
        """
        查看域名解析记录 (Read)
        
        Args:
            domain_name: 域名
            page_number: 页码，默认为 1
            page_size: 每页记录数，默认为 20，最大值 500
            
        Returns:
            解析记录列表
            
        Example:
            >>> client = AliyunDNSClient()
            >>> records = client.describe_domain_records("example.com")
            >>> for record in records:
            ...     print(f"{record['RR']}.{record['DomainName']} {record['Type']} {record['Value']}")
        """
        try:
            self.logger.info(f"查询域名 {domain_name} 的解析记录")
            
            # 构造请求
            request = alidns_models.DescribeDomainRecordsRequest(
                domain_name=domain_name,
                page_number=page_number,
                page_size=min(page_size, 500)  # 限制最大页面大小
            )
            
            # 发送请求
            response = self.client.describe_domain_records(request)
            
            # 提取记录列表
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
                        'Weight': getattr(record, 'weight', None),
                        'Locked': getattr(record, 'locked', False)
                    })
            
            self.logger.info(f"成功获取 {len(records)} 条解析记录")
            return records
            
        except Exception as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []
    
    def describe_subdomain_records(self, sub_domain: str) -> List[Dict[str, Any]]:
        """
        查看子域名解析记录 (Read)
        
        Args:
            subdomain: 子域名 (如 www.example.com)
            
        Returns:
            解析记录列表
        """
        try:
            self.logger.info(f"查询子域名 {sub_domain} 的解析记录")
            # 发送请求
            request = alidns_models.DescribeSubDomainRecordsRequest(
                sub_domain=sub_domain
            )
            response = self.client.describe_sub_domain_records(request)
            
            # 提取记录列表
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
                        'Weight': getattr(record, 'weight', None),
                        'Locked': getattr(record, 'locked', False)
                    })
            
            self.logger.info(f"成功获取 {len(records)} 条解析记录")
            return records
            
        except Exception as e:
            self.logger.error(f"查询子域名解析记录失败: {e}")
            return []

    def delete_subdomain_records(self, domain_name:str, rr:str, type_:str=None):
        """
        删除子域名的所有解析记录
        """
        try:
            request = alidns_models.DeleteSubDomainRecordsRequest(
                domain_name=domain_name,
                rr=rr,
                type=type_
            )
            response = self.client.delete_sub_domain_records(request)
            self.logger.info("删除子域名解析记录成功")
            return True
        except Exception as e:
            self.logger.error(f"删除子域名解析记录失败: {e}")
            return False
        
    def add_domain_record(self, domain_name: str, rr: str, type_: str, 
                         value: str, ttl: int = 600,
                         line: str = 'default', 
                         priority: Optional[int] = None) -> Optional[str]:
        """
        添加域名解析记录 (Create)
        
        Args:
            domain_name: 域名
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
            value: 记录值
            ttl: 生存时间，默认 600 秒
            line: 解析线路，默认 'default'
            priority: MX 记录的优先级（仅 MX 记录需要）
            
        Returns:
            新创建记录的 ID，失败时返回 None
            
        Example:
            >>> client = AliyunDNSClient()
            >>> record_id = client.add_domain_record("example.com", "www", "A", "1.2.3.4")
            >>> print(f"创建记录ID: {record_id}")
        """
        try:
            self.logger.info(f"创建DNS记录: {rr}.{domain_name} {type_} {value}")
            
            # 构造请求
            request = alidns_models.AddDomainRecordRequest(
                domain_name=domain_name,
                rr=rr,
                type=type_,
                value=value,
                ttl=ttl,
                line=line
            )
            
            # 为MX记录设置优先级
            if type_.upper() == 'MX' and priority is not None:
                request.priority = priority
            
            # 发送请求
            response = self.client.add_domain_record(request)
            
            record_id = response.body.record_id
            self.logger.info(f"DNS记录创建成功，记录ID: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"创建DNS记录失败: {e}")
            return None
    
    def update_domain_record(self, record_id: str, rr: str, type_: str, 
                           value: str, ttl: int = 600,
                           line: str = 'default',
                           priority: Optional[int] = None) -> bool:
        """
        修改域名解析记录 (Update)
        
        Args:
            record_id: 解析记录的 ID
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
            value: 记录值
            ttl: 生存时间，默认 600 秒
            line: 解析线路，默认 'default'
            priority: MX 记录的优先级（仅 MX 记录需要）
            
        Returns:
            是否修改成功
            
        Example:
            >>> client = AliyunDNSClient()
            >>> success = client.update_domain_record("123456", "www", "A", "2.3.4.5")
            >>> print(f"更新结果: {success}")
        """
        try:
            self.logger.info(f"更新DNS记录ID {record_id}: {rr} {type_} {value}")
            
            # 构造请求
            request = alidns_models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=type_,
                value=value,
                ttl=ttl,
                line=line
            )
            
            # 为MX记录设置优先级
            if type_.upper() == 'MX' and priority is not None:
                request.priority = priority
            
            # 发送请求
            response = self.client.update_domain_record(request)
            
            self.logger.info("DNS记录更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"更新DNS记录失败: {e}")
            return False
    
    def delete_domain_record(self, record_id: str) -> bool:
        """
        删除域名解析记录 (Delete)
        
        Args:
            record_id: 解析记录的 ID
            
        Returns:
            是否删除成功
            
        Example:
            >>> client = AliyunDNSClient()
            >>> success = client.delete_domain_record("123456")
            >>> print(f"删除结果: {success}")
        """
        try:
            self.logger.info(f"删除DNS记录ID: {record_id}")
            
            # 构造请求
            request = alidns_models.DeleteDomainRecordRequest(
                record_id=record_id
            )
            
            # 发送请求
            response = self.client.delete_domain_record(request)
            
            self.logger.info("DNS记录删除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"删除DNS记录失败: {e}")
            return False
    
    def set_domain_record_status(self, record_id: str, status: str) -> bool:
        """
        设置域名解析记录状态 (Update)
        
        Args:
            record_id: 解析记录的 ID
            status: 状态值，ENABLE 或 DISABLE
            
        Returns:
            是否设置成功
        """
        try:
            self.logger.info(f"设置DNS记录状态: {record_id} {status}")
            
            # 构造请求
            request = alidns_models.SetDomainRecordStatusRequest(
                record_id=record_id,
                status=status
            )
            
            # 发送请求
            response = self.client.set_domain_record_status(request)
            
            self.logger.info("DNS记录状态设置成功")
            return True
            
        except Exception as e:
            self.logger.error(f"设置DNS记录状态失败: {e}")
            return False

    def delete_subdomain_records(self, domain_name:str, rr:str, type_:str=None):
        """
        删除子域名的所有解析记录
        """
        try:
            request = alidns_models.DeleteSubDomainRecordsRequest(
                sub_domain=f"{rr}.{domain_name}",
                type=type_
            )
            response = self.client.delete_sub_domain_records(request)
            self.logger.info("删除子域名解析记录成功")
            return True
        except Exception as e:
            self.logger.error(f"删除子域名解析记录失败: {e}")
            return False

    def set_record_value(self, domain_name: str, rr: str, type_: str,
                        value: str, ttl: int = 600) -> bool:
        """
        设置DNS记录值（如果不存在则创建，存在则更新）
        
        Args:
            sub_domain: 子域名
            type_: 记录类型
            value: 记录值
            ttl: TTL值，默认600秒
            
        Returns:
            是否操作成功
        """
        try:
            # 先查找现有记录
            records = self.describe_subdomain_records(sub_domain=f"{rr}.{domain_name}")
            # records = [record for record in records if record['Type'] == type_]
            if not len(records):
                return self.add_domain_record(
                    domain_name=domain_name,
                    rr=rr,
                    type_=type_,
                    value=value,
                    ttl=ttl
                )
            if len(records) > 1:
                self.logger.warning(f"子域名 {rr}.{domain_name} 存在多个 {type_} 记录")
                for record in records:
                    self.logger.info(f"- {record['RecordId']} {record['RR']} {record['Type']} {record['Value']}")
                return False
            record = records[0]
            # 更新现有记录
            return self.update_domain_record(
                record_id=record['RecordId'],
                rr=record['RR'],
                type_=type_,
                value=value,
                ttl=ttl
            )
                
        except Exception as e:
            self.logger.error(f"设置DNS记录失败: {e}")
            return False

    def delete_record_value(self, domain_name: str, rr: str=None, type_: str=None):
        """
        删除子域名的指定类型解析记录
        """
        try:
            records = self.describe_subdomain_records(sub_domain=f"{rr}.{domain_name}")
            if type_ is not None:
                records = [record for record in records if record['Type'] == type_]
            if not len(records):
                return True
            for record in records:
                self.delete_domain_record(record['RecordId'])
                self.logger.info(f"删除子域名解析记录 {record['RecordId']} 成功")
            return True
        except Exception as e:
            self.logger.error(f"删除子域名解析记录失败: {e}")
            return False
    