#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import List, Dict, Optional, Any

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models

from chattool.utils import TencentConfig
from .base import DNSClient

class TencentDNSClient(DNSClient):
    """
    腾讯云 DNSPod 客户端 - 基于官方SDK
    """
    
    def __init__(self, 
                 secret_id: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 region: str = None,
                 endpoint: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        
        super().__init__(logger=logger)
        
        # 参数验证和环境变量回退
        self.region = region or TencentConfig.TENCENT_REGION_ID.value or "ap-guangzhou"
        self.secret_id = secret_id or TencentConfig.TENCENT_SECRET_ID.value
        self.secret_key = secret_key or TencentConfig.TENCENT_SECRET_KEY.value
        
        if not all([self.secret_id, self.secret_key]):
            raise ValueError("secret_id 和 secret_key 不能为空，请通过参数传入或设置环境变量")
        
        # 初始化官方SDK客户端
        try:
            cred = credential.Credential(self.secret_id, self.secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = endpoint or "dnspod.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            self.client = dnspod_client.DnspodClient(cred, region, clientProfile)
            self.logger.info("腾讯云DNSPod官方SDK客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化腾讯云DNSPod SDK客户端失败: {e}")
            raise

    def describe_domains(self, page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        获取域名列表
        
        Args:
            page_number: 页码，默认1
            page_size: 每页数量，默认20
            
        Returns:
            域名列表
        """
        try:
            req = models.DescribeDomainListRequest()
            req.Offset = (page_number - 1) * page_size
            req.Limit = min(page_size, 3000)
            
            resp = self.client.DescribeDomainList(req)
            
            domains = []
            if resp.DomainList:
                for domain in resp.DomainList:
                    domains.append({
                        'DomainId': domain.DomainId,
                        'DomainName': domain.Name,
                        'Status': domain.Status,
                        'RecordCount': domain.RecordCount,
                        'CreatedOn': domain.CreatedOn,
                        'Remark': domain.Remark,
                    })
            return domains
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
        try:
            req = models.DescribeRecordListRequest()
            req.Domain = domain_name
            req.Offset = (page_number - 1) * page_size
            req.Limit = min(page_size, 3000)
            
            # 支持额外的过滤参数
            if 'subdomain' in kwargs:
                req.Subdomain = kwargs['subdomain']
            if 'record_type' in kwargs:
                req.RecordType = kwargs['record_type']
            
            resp = self.client.DescribeRecordList(req)
            
            records = []
            if resp.RecordList:
                for record in resp.RecordList:
                    records.append({
                        'DomainName': domain_name,
                        'RecordId': str(record.RecordId), # 统一转为字符串
                        'RR': record.Name,
                        'Type': record.Type,
                        'Value': record.Value,
                        'TTL': record.TTL,
                        'Priority': record.MX,
                        'Line': record.Line,
                        'Status': record.Status,
                        'Remark': record.Remark,
                        'UpdatedOn': record.UpdatedOn,
                    })
            return records
        except TencentCloudSDKException as e:
            if e.code == 'ResourceNotFound.NoDataOfRecord':
                self.logger.info(f"没有找到记录: {domain_name} {kwargs.get('subdomain', '')}")
                return []
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []

    def describe_subdomain_records(self, domain_name: str, rr: str) -> List[Dict[str, Any]]:
        """覆盖基类方法，使用 DescribeRecordList 的 Subdomain 参数"""
        return self.describe_domain_records(domain_name, subdomain=rr)

    def add_domain_record(self, domain_name: str, rr: str, type_: str, value: str, ttl: int = 600, **kwargs) -> Optional[str]:
        """
        添加域名解析记录
        
        Args:
            domain_name: 域名名称
            rr: 主机记录
            type_: 记录类型
            value: 记录值
            ttl: TTL值
            **kwargs: 可选参数
            
        Returns:
            记录ID，失败返回None
        """
        try:
            req = models.CreateRecordRequest()
            req.Domain = domain_name
            req.RecordType = type_
            req.RecordLine = kwargs.get('line', '默认')
            req.Value = value
            req.TTL = ttl
            
            if rr != '@':
                req.SubDomain = rr
                
            if kwargs.get('priority') is not None:
                req.MX = kwargs.get('priority')
            
            resp = self.client.CreateRecord(req)
            return str(resp.RecordId)
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
            domain_name: 域名名称 (腾讯云API必须)
            ttl: TTL值
            **kwargs: 可选参数
            
        Returns:
            是否成功
        """
        if not domain_name:
            self.logger.error("腾讯云更新记录需要提供 domain_name")
            return False
            
        try:
            req = models.ModifyRecordRequest()
            req.Domain = domain_name
            req.RecordId = int(record_id) # 腾讯云SDK通常需要int类型的RecordId
            req.RecordType = type_
            req.RecordLine = kwargs.get('line', '默认')
            req.Value = value
            req.TTL = ttl
            
            if rr != '@':
                req.SubDomain = rr
                
            if kwargs.get('priority') is not None:
                req.MX = kwargs.get('priority')
                
            self.client.ModifyRecord(req)
            return True
        except Exception as e:
            self.logger.error(f"更新DNS记录失败: {e}")
            return False

    def delete_domain_record(self, record_id: str, domain_name: str = None) -> bool:
        """
        删除域名解析记录
        
        Args:
            record_id: 记录ID
            domain_name: 域名名称 (腾讯云API必须)
            
        Returns:
            是否成功
        """
        if not domain_name:
            self.logger.error("腾讯云删除记录需要提供 domain_name")
            return False
            
        try:
            req = models.DeleteRecordRequest()
            req.Domain = domain_name
            req.RecordId = int(record_id)
            
            self.client.DeleteRecord(req)
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
            records = self.describe_domain_records(domain_name, subdomain=rr, record_type=type_)
            
            deleted_count = 0
            for record in records:
                if value is None or record['Value'] == value:
                    if self.delete_domain_record(record['RecordId'], domain_name=domain_name):
                        deleted_count += 1
            
            return deleted_count > 0
        except Exception as e:
            self.logger.error(f"批量删除DNS记录失败: {e}")
            return False
