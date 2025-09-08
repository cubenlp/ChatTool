#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DNS 客户端

基于阿里云 DNS API 实现域名解析记录的 CRUD 操作，包括：
- 查看解析记录 (DescribeDomainRecords)
- 创建解析记录 (AddDomainRecord)
- 修改解析记录 (UpdateDomainRecord)  
- 删除解析记录 (DeleteDomainRecord)
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import httpx
from .config import AliyunDNSConfig
from batch_executor import setup_logger

class AliyunDNSClient:
    """
    阿里云 DNS 客户端
    
    提供域名解析记录的完整 CRUD 操作功能，支持同步和异步调用方式。
    """
    def __init__(self, access_key_id: Optional[str] = None, 
                 access_key_secret: Optional[str] = None,
                 region_id: str = "cn-hangzhou"):
        """
        初始化阿里云 DNS 客户端
        
        Args:
            access_key_id: 阿里云 Access Key ID，如果为空则从环境变量获取
            access_key_secret: 阿里云 Access Key Secret，如果为空则从环境变量获取
            region_id: 区域 ID，默认为 cn-hangzhou
            logger: 日志记录器，如果为空则创建默认记录器
        
        Raises:
            ValueError: 当认证信息不完整时抛出异常
        """
        # 参数验证和环境变量回退
        self.access_key_id = access_key_id or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        self.region_id = region_id or os.getenv('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou')
        
        if not all([self.access_key_id, self.access_key_secret]):
            raise ValueError("access_key_id 和 access_key_secret 不能为空，请通过参数传入或设置环境变量")
        
        # 初始化配置
        self.config = AliyunDNSConfig(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id
        )
        
        # 设置日志记录器
        self.logger = setup_logger(__name__)
        
        # HTTP 客户端配置
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
    
    def _generate_signature(self, method: str, params: Dict[str, Any]) -> str:
        """
        生成阿里云 API 签名
        
        Args:
            method: HTTP 方法
            params: 请求参数
            
        Returns:
            生成的签名字符串
        """
        # 公共参数
        common_params = {
            'Format': 'JSON',
            'Version': '2015-01-09',
            'AccessKeyId': self.access_key_id,
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0',
            'SignatureNonce': str(int(time.time() * 1000)),
            'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        # 合并参数
        all_params = {**common_params, **params}
        
        # 参数排序和编码
        sorted_params = sorted(all_params.items())
        query_string = '&'.join([
            f"{urllib.parse.quote_plus(str(k))}={urllib.parse.quote_plus(str(v))}"
            for k, v in sorted_params
        ])
        
        # 构造签名字符串
        string_to_sign = f"{method}&%2F&{urllib.parse.quote_plus(query_string)}"
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                (self.access_key_secret + '&').encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def _make_request(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 API 请求
        
        Args:
            action: API 动作名称
            params: 请求参数
            
        Returns:
            API 响应数据
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        # 添加动作参数
        request_params = {'Action': action, **params}
        
        # 生成签名
        signature = self._generate_signature('GET', request_params)
        request_params['Signature'] = signature
        
        # 构造请求 URL
        query_string = '&'.join([
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k, v in request_params.items()
        ])
        url = f"{self.config.api_base}?{query_string}"
        
        self.logger.debug(f"发送请求: {action} - {url}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查 API 错误
                if 'Code' in data:
                    error_msg = f"API 错误: {data.get('Code')} - {data.get('Message', '未知错误')}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                
                self.logger.debug(f"请求成功: {action}")
                return data
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 请求失败: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"网络请求错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"响应解析失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _make_request_async(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送异步 API 请求
        
        Args:
            action: API 动作名称  
            params: 请求参数
            
        Returns:
            API 响应数据
        """
        # 添加动作参数
        request_params = {'Action': action, **params}
        
        # 生成签名
        signature = self._generate_signature('GET', request_params)
        request_params['Signature'] = signature
        
        # 构造请求 URL
        query_string = '&'.join([
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k, v in request_params.items()
        ])
        url = f"{self.config.api_base}?{query_string}"
        
        self.logger.debug(f"发送异步请求: {action} - {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查 API 错误
                if 'Code' in data:
                    error_msg = f"API 错误: {data.get('Code')} - {data.get('Message', '未知错误')}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                
                self.logger.debug(f"异步请求成功: {action}")
                return data
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 请求失败: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"网络请求错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"响应解析失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    # ==================== CRUD 操作接口 ====================
    
    def describe_domain_records(self, domain_name: str, 
                              rr: Optional[str] = None,
                              type_: Optional[str] = None,
                              page_number: int = 1,
                              page_size: int = 20) -> List[Dict[str, Any]]:
        """
        查看域名解析记录 (Read)
        
        Args:
            domain_name: 域名
            rr: 主机记录，可选过滤条件
            type_: 解析记录类型，可选过滤条件 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
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
            
            params = {
                'DomainName': domain_name,
                'PageNumber': page_number,
                'PageSize': min(page_size, 500)  # 限制最大页面大小
            }
            
            # 添加可选过滤条件
            if rr:
                params['RRKeyWord'] = rr
            if type_:
                params['TypeKeyWord'] = type_
            
            response = self._make_request('DescribeDomainRecords', params)
            
            # 提取记录列表
            domain_records = response.get('DomainRecords', {})
            records = domain_records.get('Record', [])
            
            self.logger.info(f"成功获取 {len(records)} 条解析记录")
            return records
            
        except Exception as e:
            self.logger.error(f"查询域名解析记录失败: {e}")
            return []
    
    def add_domain_record(self, domain_name: str, rr: str, type_: str, 
                         value: str, ttl: int = 600,
                         line: str = "default", priority: Optional[int] = None) -> Optional[str]:
        """
        创建域名解析记录 (Create)
        
        Args:
            domain_name: 域名
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
            value: 记录值 (IP地址或域名)
            ttl: 生存时间，默认 600 秒，最小值 600
            line: 解析线路，默认为 default
            priority: 优先级，仅 MX 和 SRV 记录需要
            
        Returns:
            新建记录的 RecordId，失败时返回 None
            
        Example:
            >>> client = AliyunDNSClient()
            >>> record_id = client.add_domain_record("example.com", "www", "A", "192.168.1.1")
            >>> print(f"创建的记录 ID: {record_id}")
        """
        try:
            self.logger.info(f"为域名 {domain_name} 添加解析记录: {rr} {type_} {value}")
            
            params = {
                'DomainName': domain_name,
                'RR': rr,
                'Type': type_,
                'Value': value,
                'TTL': max(ttl, 600),  # 确保 TTL 不小于 600
                'Line': line
            }
            
            # MX 和 SRV 记录需要优先级
            if type_ in ['MX', 'SRV'] and priority is not None:
                params['Priority'] = priority
            elif type_ in ['MX', 'SRV']:
                params['Priority'] = 10  # 默认优先级
            
            response = self._make_request('AddDomainRecord', params)
            
            record_id = response.get('RecordId')
            if record_id:
                self.logger.info(f"成功创建解析记录，记录 ID: {record_id}")
                return record_id
            else:
                self.logger.warning("创建解析记录成功但未返回记录 ID")
                return None
                
        except Exception as e:
            self.logger.error(f"创建域名解析记录失败: {e}")
            return None
    
    def update_domain_record(self, record_id: str, rr: str, type_: str,
                           value: str, ttl: int = 600,
                           line: str = "default", priority: Optional[int] = None) -> bool:
        """
        修改域名解析记录 (Update)
        
        Args:
            record_id: 解析记录 ID
            rr: 主机记录 (如 www, @, *)
            type_: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
            value: 记录值 (IP地址或域名)
            ttl: 生存时间，默认 600 秒，最小值 600
            line: 解析线路，默认为 default
            priority: 优先级，仅 MX 和 SRV 记录需要
            
        Returns:
            操作是否成功
            
        Example:
            >>> client = AliyunDNSClient()
            >>> success = client.update_domain_record("123456789", "www", "A", "192.168.1.100")
            >>> print(f"更新结果: {'成功' if success else '失败'}")
        """
        try:
            self.logger.info(f"更新解析记录 {record_id}: {rr} {type_} {value}")
            
            params = {
                'RecordId': record_id,
                'RR': rr,
                'Type': type_,
                'Value': value,
                'TTL': max(ttl, 600),  # 确保 TTL 不小于 600
                'Line': line
            }
            
            # MX 和 SRV 记录需要优先级
            if type_ in ['MX', 'SRV'] and priority is not None:
                params['Priority'] = priority
            elif type_ in ['MX', 'SRV']:
                params['Priority'] = 10  # 默认优先级
            
            response = self._make_request('UpdateDomainRecord', params)
            
            # 检查是否有 RecordId 返回（表示成功）
            if response.get('RecordId'):
                self.logger.info(f"成功更新解析记录 {record_id}")
                return True
            else:
                self.logger.warning(f"更新解析记录 {record_id} 可能失败：未返回记录 ID")
                return False
                
        except Exception as e:
            self.logger.error(f"更新域名解析记录失败: {e}")
            return False
    
    def delete_domain_record(self, record_id: str) -> bool:
        """
        删除域名解析记录 (Delete)
        
        Args:
            record_id: 解析记录 ID
            
        Returns:
            操作是否成功
            
        Example:
            >>> client = AliyunDNSClient()
            >>> success = client.delete_domain_record("123456789")
            >>> print(f"删除结果: {'成功' if success else '失败'}")
        """
        try:
            self.logger.info(f"删除解析记录 {record_id}")
            
            params = {'RecordId': record_id}
            
            response = self._make_request('DeleteDomainRecord', params)
            
            # 检查是否有 RecordId 返回（表示成功）
            if response.get('RecordId'):
                self.logger.info(f"成功删除解析记录 {record_id}")
                return True
            else:
                self.logger.warning(f"删除解析记录 {record_id} 可能失败：未返回记录 ID")
                return False
                
        except Exception as e:
            self.logger.error(f"删除域名解析记录失败: {e}")
            return False
    
    # ==================== 异步版本接口 ====================
    
    async def describe_domain_records_async(self, domain_name: str,
                                          rr: Optional[str] = None,
                                          type_: Optional[str] = None,
                                          page_number: int = 1,
                                          page_size: int = 20) -> List[Dict[str, Any]]:
        """查看域名解析记录的异步版本"""
        try:
            self.logger.info(f"异步查询域名 {domain_name} 的解析记录")
            
            params = {
                'DomainName': domain_name,
                'PageNumber': page_number,
                'PageSize': min(page_size, 500)
            }
            
            if rr:
                params['RRKeyWord'] = rr
            if type_:
                params['TypeKeyWord'] = type_
            
            response = await self._make_request_async('DescribeDomainRecords', params)
            
            domain_records = response.get('DomainRecords', {})
            records = domain_records.get('Record', [])
            
            self.logger.info(f"异步成功获取 {len(records)} 条解析记录")
            return records
            
        except Exception as e:
            self.logger.error(f"异步查询域名解析记录失败: {e}")
            return []
    
    async def add_domain_record_async(self, domain_name: str, rr: str, type_: str,
                                    value: str, ttl: int = 600,
                                    line: str = "default", priority: Optional[int] = None) -> Optional[str]:
        """创建域名解析记录的异步版本"""
        try:
            self.logger.info(f"异步为域名 {domain_name} 添加解析记录: {rr} {type_} {value}")
            
            params = {
                'DomainName': domain_name,
                'RR': rr,
                'Type': type_,
                'Value': value,
                'TTL': max(ttl, 600),
                'Line': line
            }
            
            if type_ in ['MX', 'SRV'] and priority is not None:
                params['Priority'] = priority
            elif type_ in ['MX', 'SRV']:
                params['Priority'] = 10
            
            response = await self._make_request_async('AddDomainRecord', params)
            
            record_id = response.get('RecordId')
            if record_id:
                self.logger.info(f"异步成功创建解析记录，记录 ID: {record_id}")
                return record_id
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"异步创建域名解析记录失败: {e}")
            return None
    
    async def update_domain_record_async(self, record_id: str, rr: str, type_: str,
                                       value: str, ttl: int = 600,
                                       line: str = "default", priority: Optional[int] = None) -> bool:
        """修改域名解析记录的异步版本"""
        try:
            self.logger.info(f"异步更新解析记录 {record_id}: {rr} {type_} {value}")
            
            params = {
                'RecordId': record_id,
                'RR': rr,
                'Type': type_,
                'Value': value,
                'TTL': max(ttl, 600),
                'Line': line
            }
            
            if type_ in ['MX', 'SRV'] and priority is not None:
                params['Priority'] = priority
            elif type_ in ['MX', 'SRV']:
                params['Priority'] = 10
            
            response = await self._make_request_async('UpdateDomainRecord', params)
            
            if response.get('RecordId'):
                self.logger.info(f"异步成功更新解析记录 {record_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"异步更新域名解析记录失败: {e}")
            return False
    
    async def delete_domain_record_async(self, record_id: str) -> bool:
        """删除域名解析记录的异步版本"""
        try:
            self.logger.info(f"异步删除解析记录 {record_id}")
            
            params = {'RecordId': record_id}
            
            response = await self._make_request_async('DeleteDomainRecord', params)
            
            if response.get('RecordId'):
                self.logger.info(f"异步成功删除解析记录 {record_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"异步删除域名解析记录失败: {e}")
            return False
    
    # ==================== 便利方法 ====================
    
    def find_record_by_rr(self, domain_name: str, rr: str, type_: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        根据主机记录查找解析记录
        
        Args:
            domain_name: 域名
            rr: 主机记录
            type_: 记录类型，可选
            
        Returns:
            匹配的第一条记录，未找到时返回 None
        """
        records = self.describe_domain_records(domain_name, rr=rr, type_=type_)
        if records:
            return records[0]
        return None
    
    def get_all_records(self, domain_name: str) -> List[Dict[str, Any]]:
        """
        获取域名的所有解析记录（自动翻页）
        
        Args:
            domain_name: 域名
            
        Returns:
            所有解析记录列表
        """
        all_records = []
        page_number = 1
        page_size = 500  # 使用最大页面大小提高效率
        
        while True:
            records = self.describe_domain_records(
                domain_name, page_number=page_number, page_size=page_size
            )
            
            if not records:
                break
                
            all_records.extend(records)
            
            # 如果返回的记录数少于页面大小，说明已经是最后一页
            if len(records) < page_size:
                break
                
            page_number += 1
        
        self.logger.info(f"获取域名 {domain_name} 的全部 {len(all_records)} 条解析记录")
        return all_records
    
    def update_record_by_rr(self, domain_name: str, rr: str, type_: str,
                           new_value: str, ttl: int = 600) -> bool:
        """
        根据主机记录更新解析记录
        
        Args:
            domain_name: 域名
            rr: 主机记录
            type_: 记录类型
            new_value: 新的记录值
            ttl: TTL值
            
        Returns:
            操作是否成功
        """
        # 先查找记录
        record = self.find_record_by_rr(domain_name, rr, type_)
        if not record:
            self.logger.warning(f"未找到匹配的解析记录: {domain_name} {rr} {type_}")
            return False
        
        # 更新记录
        record_id = record['RecordId']
        return self.update_domain_record(
            record_id=record_id,
            rr=rr,
            type_=type_,
            value=new_value,
            ttl=ttl
        )
    
    def delete_record_by_rr(self, domain_name: str, rr: str, type_: Optional[str] = None) -> bool:
        """
        根据主机记录删除解析记录
        
        Args:
            domain_name: 域名
            rr: 主机记录
            type_: 记录类型，可选
            
        Returns:
            操作是否成功
        """
        # 先查找记录
        record = self.find_record_by_rr(domain_name, rr, type_)
        if not record:
            self.logger.warning(f"未找到匹配的解析记录: {domain_name} {rr} {type_ or '(任意类型)'}")
            return False
        
        # 删除记录
        record_id = record['RecordId']
        return self.delete_domain_record(record_id)
