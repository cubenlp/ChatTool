#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP工具函数实现

基于现有的AliyunDNSClient等类实现MCP工具函数。
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from chattool.tools.aliyun_dns import AliyunDNSClient, DynamicIPUpdater, SSLCertUpdater

# Pydantic模型定义
class DomainRecord(BaseModel):
    """域名解析记录模型"""
    domain_name: str = Field(description="域名")
    record_id: Optional[str] = Field(None, description="记录ID")
    rr: str = Field(description="主机记录")
    type: str = Field(description="记录类型 (A, AAAA, CNAME, MX, TXT等)")
    value: str = Field(description="记录值")
    ttl: int = Field(default=600, description="生存时间（秒）")
    priority: Optional[int] = Field(None, description="MX记录优先级")
    line: str = Field(default="default", description="解析线路")
    status: str = Field(default="ENABLE", description="记录状态")


class DynamicIPConfig(BaseModel):
    """动态IP配置模型"""
    domain_name: str = Field(description="域名")
    rr: str = Field(description="子域名记录")
    record_type: str = Field(default="A", description="DNS记录类型")
    dns_ttl: int = Field(default=600, description="TTL值")
    check_interval: int = Field(default=120, description="检查间隔（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=5, description="重试延迟（秒）")


class SSLCertConfig(BaseModel):
    """SSL证书配置模型"""
    domains: List[str] = Field(description="域名列表")
    email: str = Field(description="Let's Encrypt账户邮箱")
    cert_dir: str = Field(default="/etc/ssl/certs", description="证书存储目录")
    private_key_dir: str = Field(default="/etc/ssl/private", description="私钥存储目录")
    staging: bool = Field(default=False, description="是否使用测试环境")


def get_dns_client() -> AliyunDNSClient:
    """获取DNS客户端实例"""
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        raise ValueError("缺少阿里云认证信息，请设置 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET 环境变量")
    
    return AliyunDNSClient(access_key_id=access_key_id, access_key_secret=access_key_secret)


def describe_domains(page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
    """
    查看域名列表
    
    Args:
        page_number: 页码，默认为1
        page_size: 每页记录数，默认为20，最大值500
        
    Returns:
        域名列表
    """
    try:
        client = get_dns_client()
        return client.describe_domains(page_number=page_number, page_size=page_size)
    except Exception as e:
        return {"error": str(e), "domains": []}


def describe_domain_records(domain_name: str, page_number: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
    """
    查看域名解析记录
    
    Args:
        domain_name: 域名
        page_number: 页码，默认为1
        page_size: 每页记录数，默认为20，最大值500
        
    Returns:
        解析记录列表
    """
    try:
        client = get_dns_client()
        return client.describe_domain_records(domain_name=domain_name, page_number=page_number, page_size=page_size)
    except Exception as e:
        return {"error": str(e), "records": []}


def add_domain_record(domain_name: str, rr: str, record_type: str, value: str, 
                     ttl: int = 600, line: str = "default", priority: Optional[int] = None) -> Dict[str, Any]:
    """
    添加域名解析记录
    
    Args:
        domain_name: 域名
        rr: 主机记录 (如 www, @, *)
        record_type: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
        value: 记录值
        ttl: 生存时间，默认600秒
        line: 解析线路，默认 'default'
        priority: MX记录的优先级（仅MX记录需要）
        
    Returns:
        操作结果，包含新创建记录的ID
    """
    try:
        client = get_dns_client()
        record_id = client.add_domain_record(
            domain_name=domain_name,
            rr=rr,
            type_=record_type,
            value=value,
            ttl=ttl,
            line=line,
            priority=priority
        )
        return {
            "success": record_id is not None,
            "record_id": record_id,
            "message": f"DNS记录创建成功，记录ID: {record_id}" if record_id else "DNS记录创建失败"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_domain_record(record_id: str, rr: str, record_type: str, value: str,
                        ttl: int = 600, line: str = "default", priority: Optional[int] = None) -> Dict[str, Any]:
    """
    更新域名解析记录
    
    Args:
        record_id: 解析记录的ID
        rr: 主机记录 (如 www, @, *)
        record_type: 解析记录类型 (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA 等)
        value: 记录值
        ttl: 生存时间，默认600秒
        line: 解析线路，默认 'default'
        priority: MX记录的优先级（仅MX记录需要）
        
    Returns:
        操作结果
    """
    try:
        client = get_dns_client()
        success = client.update_domain_record(
            record_id=record_id,
            rr=rr,
            type_=record_type,
            value=value,
            ttl=ttl,
            line=line,
            priority=priority
        )
        return {
            "success": success,
            "message": "DNS记录更新成功" if success else "DNS记录更新失败"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_domain_record(record_id: str) -> Dict[str, Any]:
    """
    删除域名解析记录
    
    Args:
        record_id: 解析记录的ID
        
    Returns:
        操作结果
    """
    try:
        client = get_dns_client()
        success = client.delete_domain_record(record_id=record_id)
        return {
            "success": success,
            "message": "DNS记录删除成功" if success else "DNS记录删除失败"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_domain_record_status(record_id: str, status: str) -> Dict[str, Any]:
    """
    设置域名解析记录状态
    
    Args:
        record_id: 解析记录的ID
        status: 状态值，ENABLE 或 DISABLE
        
    Returns:
        操作结果
    """
    try:
        if status not in ["ENABLE", "DISABLE"]:
            return {"success": False, "error": "状态值必须为 ENABLE 或 DISABLE"}
        
        client = get_dns_client()
        success = client.set_domain_record_status(record_id=record_id, status=status)
        return {
            "success": success,
            "message": f"DNS记录状态设置为 {status} 成功" if success else f"DNS记录状态设置失败"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dynamic_ip_updater(domain_name: str, rr: str, record_type: str = "A",
                      dns_ttl: int = 600, max_retries: int = 3, 
                      retry_delay: int = 5, run_once: bool = True) -> Dict[str, Any]:
    """
    动态IP监控和DNS自动更新功能
    
    Args:
        domain_name: 域名
        rr: 子域名记录
        record_type: DNS记录类型，默认为A记录
        dns_ttl: TTL值，默认600秒
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试延迟（秒），默认5秒
        run_once: 是否只运行一次检查，默认为True
        
    Returns:
        操作结果
    """
    try:
        updater = DynamicIPUpdater(
            domain_name=domain_name,
            rr=rr,
            record_type=record_type,
            dns_ttl=dns_ttl,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        if run_once:
            # 同步运行一次检查
            result = asyncio.run(updater.run_once())
            return {
                "success": True,
                "updated": result,
                "message": "动态IP检查完成" if result else "IP地址未变化，无需更新"
            }
        else:
            # 这里应该启动后台任务，但在MCP环境中建议用户手动管理长期任务
            return {
                "success": False,
                "error": "连续监控模式需要在独立环境中运行，请使用 run_once=True 进行单次检查"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def ssl_cert_updater(domains: List[str], email: str, cert_dir: str = "/etc/ssl/certs",
                    private_key_dir: str = "/etc/ssl/private", staging: bool = False) -> Dict[str, Any]:
    """
    SSL证书自动更新和DNS挑战管理
    
    Args:
        domains: 域名列表
        email: Let's Encrypt账户邮箱
        cert_dir: 证书存储目录，默认 /etc/ssl/certs
        private_key_dir: 私钥存储目录，默认 /etc/ssl/private
        staging: 是否使用Let's Encrypt测试环境，默认False
        
    Returns:
        操作结果
    """
    try:
        if not domains:
            return {"success": False, "error": "域名列表不能为空"}
        
        if not email:
            return {"success": False, "error": "邮箱地址不能为空"}
        
        updater = SSLCertUpdater(
            domains=domains,
            email=email,
            cert_dir=cert_dir,
            private_key_dir=private_key_dir,
            staging=staging
        )
        
        # 运行证书更新检查
        result = asyncio.run(updater.run_once())
        
        return {
            "success": result,
            "domains": domains,
            "message": "SSL证书更新成功" if result else "SSL证书更新失败或无需更新",
            "staging": staging
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}