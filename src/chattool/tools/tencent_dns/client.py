#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 DNSPod 客户端 - 基于官方SDK

基于腾讯云官方 SDK 实现域名解析记录的 CRUD 操作，包括：
- 查看解析记录 (DescribeRecordList)
- 创建解析记录 (CreateRecord)  
- 修改解析记录 (ModifyRecord)
- 删除解析记录 (DeleteRecord)
- 查看域名列表 (DescribeDomainList)
"""

import os
import logging
from typing import List, Dict, Optional, Any
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models
from chattool.utils import setup_logger
from chattool.const import CHATTOOL_CONFIG_DIR

TENCENT_ENV_FILE = os.path.join(CHATTOOL_CONFIG_DIR, 'tencent.env')

class TencentDNSClient:
    """
    腾讯云 DNSPod 客户端 - 基于官方SDK
    
    提供域名解析记录的完整 CRUD 操作功能。
    """
    
    def __init__(self, secret_id: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 region: str = "ap-guangzhou",
                 endpoint: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化腾讯云 DNSPod 客户端
        
        Args:
            secret_id: 腾讯云 Secret ID，如果为空则从环境变量获取
            secret_key: 腾讯云 Secret Key，如果为空则从环境变量获取
            region: 地域，默认为 ap-guangzhou
            endpoint: API 端点，默认为 dnspod.tencentcloudapi.com
            logger: 日志记录器，如果为空则创建默认记录器
        
        Raises:
            ValueError: 当认证信息不完整时抛出异常
        """
        # 参数验证和环境变量回退
        _env_values = dotenv_values(TENCENT_ENV_FILE)
        self.region = region or _env_values.get('TENCENT_REGION_ID', os.getenv('TENCENT_REGION_ID', 'ap-guangzhou'))
        self.secret_id = secret_id or _env_values.get('TENCENT_SECRET_ID', os.getenv('TENCENT_SECRET_ID'))
        self.secret_key = secret_key or _env_values.get('TENCENT_SECRET_KEY', os.getenv('TENCENT_SECRET_KEY'))
        
        if not all([self.secret_id, self.secret_key]):
            raise ValueError("secret_id 和 secret_key 不能为空，请通过参数传入或设置环境变量")
        
        # 设置日志记录器
        self.logger = logger or setup_logger(__name__)
        
        # 初始化官方SDK客户端
        try:
            # 创建认证对象
            cred = credential.Credential(self.secret_id, self.secret_key)
            
            # 配置HTTP协议相关信息
            httpProfile = HttpProfile()
            httpProfile.endpoint = endpoint or "dnspod.tencentcloudapi.com"
            
            # 配置客户端
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # 创建客户端
            self.client = dnspod_client.DnspodClient(cred, region, clientProfile)
            self.logger.info("腾讯云DNSPod官方SDK客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化腾讯云DNSPod SDK客户端失败: {e}")
            raise
    
    def describe_domains(self, page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        查看域名列表 (Read)
        
        Args:
            page_number: 页码，默认为 1
            page_size: 每页记录数，默认为 20，最大值 3000
            
        Returns:
            域名列表
            
        Example:
            >>> client = TencentDNSClient()
            >>> domains = client.describe_domains()
            >>> for domain in domains:
            ...     print(f"{domain['Name']} ({domain['DomainId']})")
        """
        try:
            self.logger.info(f"查询域名列表")
            
            # 构造请求
            req = models.DescribeDomainListRequest()
            req.Offset = (page_number - 1) * page_size
            req.Limit = min(page_size, 3000)  # 限制最大页面大小
            
            # 发送请求
            resp = self.client.DescribeDomainList(req)
            
            # 提取域名列表
            domains = []
            if resp.DomainList:
                domain_list:List[models.DomainListItem] = resp.DomainList
                for domain in domain_list:
                    domains.append({
                        'DomainId': domain.DomainId,
                        'DomainName': domain.Name,
                        'Status': domain.Status,
                        'TTL': domain.TTL,
                        'CNAMESpeedup': domain.CNAMESpeedup,
                        'DNSStatus': domain.DNSStatus,
                        'Grade': domain.Grade,
                        'GroupId': domain.GroupId,
                        'SearchEnginePush': domain.SearchEnginePush,
                        'Remark': domain.Remark,
                        'Punycode': domain.Punycode,
                        'EffectiveDNS': domain.EffectiveDNS,
                        'GradeLevel': domain.GradeLevel,
                        'GradeTitle': domain.GradeTitle,
                        'IsVip': domain.IsVip,
                        'VipStartAt': domain.VipStartAt,
                        'VipEndAt': domain.VipEndAt,
                        'VipAutoRenew': domain.VipAutoRenew,
                        'RecordCount': domain.RecordCount,
                        'CreatedOn': domain.CreatedOn,
                        'UpdatedOn': domain.UpdatedOn,
                        'Owner': domain.Owner
                    })
            
            self.logger.info(f"成功获取 {len(domains)} 条域名列表")
            return domains
            
        except TencentCloudSDKException as e:
            self.logger.error(f"查询域名列表失败: {e}")
            return []
    
    def describe_domain_records(self, domain_name: str,
                               domain_id: Optional[int] = None,
                               subdomain: Optional[str] = None,
                               record_type: Optional[str] = None,
                               record_line: Optional[str] = None,
                               record_line_id: Optional[str] = None,
                               group_id: Optional[int] = None,
                               keyword: Optional[str] = None,
                               sort_field: Optional[str] = None,
                               sort_type: Optional[str] = None,
                               offset: int = 0,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        查看域名解析记录 (Read)
        
        Args:
            domain_name: 域名
            domain_id: 域名 ID，优先级高于 domain_name
            subdomain: 解析记录的主机头
            record_type: 记录类型，如 A，CNAME，NS，AAAA 等
            record_line: 记录线路，如 "默认"
            record_line_id: 线路 ID
            group_id: 分组 ID
            keyword: 搜索关键字
            sort_field: 排序字段
            sort_type: 排序方式，ASC 或 DESC
            offset: 偏移量，默认为 0
            limit: 限制数量，默认为 100，最大 3000
            
        Returns:
            解析记录列表
            
        Example:
            >>> client = TencentDNSClient()
            >>> records = client.describe_domain_records("example.com")
            >>> for record in records:
            ...     print(f"{record['RR']}.{domain_name} {record['Type']} {record['Value']}")
        """
        try:
            self.logger.info(f"查询域名 {domain_name} 的解析记录")
            
            # 构造请求
            req = models.DescribeRecordListRequest()
            req.Domain = domain_name
            if domain_id:
                req.DomainId = domain_id
            if subdomain:
                req.Subdomain = subdomain
            if record_type:
                req.RecordType = record_type
            if record_line:
                req.RecordLine = record_line
            if record_line_id:
                req.RecordLineId = record_line_id
            if group_id:
                req.GroupId = group_id
            if keyword:
                req.Keyword = keyword
            if sort_field:
                req.SortField = sort_field
            if sort_type:
                req.SortType = sort_type
            req.Offset = offset
            req.Limit = min(limit, 3000)  # 限制最大页面大小
            
            # 发送请求
            resp = self.client.DescribeRecordList(req)
            
            # 提取记录列表
            records = []
            if resp.RecordList:
                record_list:List[models.RecordListItem] = resp.RecordList
                for record in record_list:
                    records.append({
                        'DomainName': domain_name,
                        'RecordId': record.RecordId,
                        'RR': record.Name,
                        'Type': record.Type,
                        'Value': record.Value,
                        'TTL': record.TTL,
                        'Priority': record.MX,
                        'Line': record.Line,
                        'LineId': record.LineId,
                        'Status': record.Status,
                        'Weight': record.Weight,
                        'MonitorStatus': record.MonitorStatus,
                        'Remark': record.Remark,
                        'UpdatedOn': record.UpdatedOn,
                        'Locked': False  # 腾讯云API没有直接的锁定字段
                    })
            
            self.logger.info(f"成功获取 {len(records)} 条解析记录")
            return records
            
        except TencentCloudSDKException as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []
    
    def describe_subdomain_records(self, sub_domain: str) -> List[Dict[str, Any]]:
        """
        查看子域名解析记录 (Read)
        
        Args:
            sub_domain: 子域名 (如 www.example.com)
            
        Returns:
            解析记录列表
        """
        try:
            # 从子域名中提取域名和主机记录
            parts = sub_domain.split('.')
            if len(parts) < 2:
                raise ValueError("子域名格式不正确")
            
            # 假设最后两部分是主域名，前面是子域名
            if len(parts) == 2:
                # 这是根域名
                domain_name = sub_domain
                subdomain = None
            else:
                domain_name = '.'.join(parts[-2:])
                subdomain = '.'.join(parts[:-2])
            
            self.logger.info(f"查询子域名 {sub_domain} 的解析记录")
            
            return self.describe_domain_records(
                domain_name=domain_name,
                subdomain=subdomain
            )
            
        except Exception as e:
            self.logger.error(f"查询子域名解析记录失败: {e}")
            return []
    
    def add_domain_record(self, domain_name: str, rr: str, type_: str, 
                         value: str, ttl: int = 600,
                         line: str = '默认', 
                         priority: Optional[int] = None,
                         weight: Optional[int] = None,
                         status: str = "ENABLE",
                         remark: Optional[str] = None) -> Optional[int]:
        """
        添加域名解析记录 (Create)
        
        Args:
            domain_name: 域名
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
            value: 记录值
            ttl: 生存时间，默认 600 秒
            line: 解析线路，默认 '默认'
            priority: MX 记录的优先级（仅 MX 记录需要）
            weight: 权重信息
            status: 记录状态，ENABLE 或 DISABLE
            remark: 备注
            
        Returns:
            新创建记录的 ID，失败时返回 None
            
        Example:
            >>> client = TencentDNSClient()
            >>> record_id = client.add_domain_record("example.com", "www", "A", "1.2.3.4")
            >>> print(f"创建记录ID: {record_id}")
        """
        try:
            self.logger.info(f"创建DNS记录: {rr}.{domain_name} {type_} {value}")
            
            # 构造请求
            req = models.CreateRecordRequest()
            req.Domain = domain_name
            req.RecordType = type_
            req.RecordLine = line
            req.Value = value
            
            if rr != '@':
                req.SubDomain = rr
            if ttl:
                req.TTL = ttl
            if priority is not None:
                req.MX = priority
            if weight is not None:
                req.Weight = weight
            if status:
                req.Status = status
            if remark:
                req.Remark = remark
            
            # 发送请求
            resp = self.client.CreateRecord(req)
            
            record_id = resp.RecordId
            self.logger.info(f"DNS记录创建成功，记录ID: {record_id}")
            return record_id
            
        except TencentCloudSDKException as e:
            self.logger.error(f"创建DNS记录失败: {e}")
            return None
    
    def update_domain_record(self, record_id: int, rr: str, type_: str, 
                           value: str, domain_name: str, ttl: int = 600,
                           line: str = '默认',
                           priority: Optional[int] = None,
                           weight: Optional[int] = None,
                           status: str = "ENABLE",
                           remark: Optional[str] = None) -> bool:
        """
        修改域名解析记录 (Update)
        
        Args:
            record_id: 解析记录的 ID
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
            value: 记录值
            domain_name: 域名
            ttl: 生存时间，默认 600 秒
            line: 解析线路，默认 '默认'
            priority: MX 记录的优先级（仅 MX 记录需要）
            weight: 权重信息
            status: 记录状态
            remark: 备注
            
        Returns:
            是否修改成功
            
        Example:
            >>> client = TencentDNSClient()
            >>> success = client.update_domain_record(123456, "www", "A", "2.3.4.5", "example.com")
            >>> print(f"更新结果: {success}")
        """
        try:
            self.logger.info(f"更新DNS记录ID {record_id}: {rr} {type_} {value}")
            
            # 构造请求
            req = models.ModifyRecordRequest()
            req.Domain = domain_name
            req.RecordId = record_id
            req.RecordType = type_
            req.RecordLine = line
            req.Value = value
            
            if rr != '@':
                req.SubDomain = rr
            if ttl:
                req.TTL = ttl
            if priority is not None:
                req.MX = priority
            if weight is not None:
                req.Weight = weight
            if status:
                req.Status = status
            if remark:
                req.Remark = remark
            
            # 发送请求
            resp = self.client.ModifyRecord(req)
            
            self.logger.info("DNS记录更新成功")
            return True
            
        except TencentCloudSDKException as e:
            self.logger.error(f"更新DNS记录失败: {e}")
            return False
    
    def delete_domain_record(self, record_id: int, domain_name: str) -> bool:
        """
        删除域名解析记录 (Delete)
        
        Args:
            record_id: 解析记录的 ID
            domain_name: 域名
            
        Returns:
            是否删除成功
            
        Example:
            >>> client = TencentDNSClient()
            >>> success = client.delete_domain_record(123456, "example.com")
            >>> print(f"删除结果: {success}")
        """
        try:
            self.logger.info(f"删除DNS记录ID: {record_id}")
            
            # 构造请求
            req = models.DeleteRecordRequest()
            req.Domain = domain_name
            req.RecordId = record_id
            
            # 发送请求
            resp = self.client.DeleteRecord(req)
            
            self.logger.info("DNS记录删除成功")
            return True
            
        except TencentCloudSDKException as e:
            self.logger.error(f"删除DNS记录失败: {e}")
            return False
    
    def set_domain_record_status(self, record_id: int, status: str, domain_name: str) -> bool:
        """
        设置域名解析记录状态 (Update)
        
        Args:
            record_id: 解析记录的 ID
            status: 状态值，ENABLE 或 DISABLE
            domain_name: 域名
            
        Returns:
            是否设置成功
        """
        try:
            self.logger.info(f"设置DNS记录状态: {record_id} {status}")
            
            # 构造请求
            req = models.ModifyRecordStatusRequest()
            req.Domain = domain_name
            req.RecordId = record_id
            req.Status = status
            
            # 发送请求
            resp = self.client.ModifyRecordStatus(req)
            
            self.logger.info("DNS记录状态设置成功")
            return True
            
        except TencentCloudSDKException as e:
            self.logger.error(f"设置DNS记录状态失败: {e}")
            return False

    def delete_subdomain_records(self, domain_name: str, rr: str, type_: str = None):
        """
        删除子域名的所有解析记录
        """
        try:
            # 先查找记录
            records = self.describe_domain_records(
                domain_name=domain_name,
                subdomain=rr,
                record_type=type_
            )
            
            if not records:
                self.logger.info("没有找到匹配的记录")
                return True
            
            success = True
            for record in records:
                if not self.delete_domain_record(record['RecordId'], domain_name):
                    success = False
                else:
                    self.logger.info(f"删除子域名解析记录 {record['RecordId']} 成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除子域名解析记录失败: {e}")
            return False
        
    def set_record_value(self, domain_name: str, rr: str, type_: str,
                        value: str, ttl: int = 600) -> bool:
        """
        设置DNS记录值（如果不存在则创建，存在则更新）
        
        Args:
            domain_name: 域名
            rr: 主机记录
            type_: 记录类型
            value: 记录值
            ttl: TTL值，默认600秒
            
        Returns:
            是否操作成功
        """
        try:
            # 先查找现有记录
            records = self.describe_domain_records(
                domain_name=domain_name,
                subdomain=rr,
                record_type=type_
            )
            
            if not records:
                # 不存在，创建新记录
                record_id = self.add_domain_record(
                    domain_name=domain_name,
                    rr=rr,
                    type_=type_,
                    value=value,
                    ttl=ttl
                )
                return record_id is not None
                
            if len(records) > 1:
                self.logger.warning(f"子域名 {rr}.{domain_name} 存在多个 {type_} 记录")
                for record in records:
                    self.logger.info(f"- {record['RecordId']} {record['RR']} {record['Type']} {record['Value']}")
                return False
            
            # 存在唯一记录，更新
            record = records[0]
            return self.update_domain_record(
                record_id=record['RecordId'],
                rr=record['RR'],
                type_=type_,
                value=value,
                domain_name=domain_name,
                ttl=ttl
            )
                
        except Exception as e:
            self.logger.error(f"设置DNS记录失败: {e}")
            return False

    def delete_record_value(self, domain_name: str, rr: str = None, type_: str = None):
        """
        删除子域名的指定类型解析记录
        """
        try:
            records = self.describe_domain_records(
                domain_name=domain_name,
                subdomain=rr,
                record_type=type_
            )
            
            if not records:
                self.logger.info("没有找到匹配的记录")
                return True
                
            success = True
            for record in records:
                if not self.delete_domain_record(record['RecordId'], domain_name):
                    success = False
                else:
                    self.logger.info(f"删除解析记录 {record['RecordId']} 成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除解析记录失败: {e}")
            return False
