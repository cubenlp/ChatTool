#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP辅助工具函数

提供通用辅助功能，如输入验证、格式化、错误处理等。
"""

import re
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path


def format_dns_record(record: Dict[str, Any]) -> str:
    """
    格式化DNS记录为易读的字符串
    
    Args:
        record: DNS记录字典
        
    Returns:
        格式化的DNS记录字符串
    """
    if not record:
        return "空记录"
    
    # 基本信息
    domain = record.get('DomainName', 'N/A')
    rr = record.get('RR', 'N/A')
    record_type = record.get('Type', 'N/A')
    value = record.get('Value', 'N/A')
    ttl = record.get('TTL', 'N/A')
    status = record.get('Status', 'N/A')
    
    # 构建完整域名
    if rr == '@':
        full_domain = domain
    else:
        full_domain = f"{rr}.{domain}"
    
    # 格式化输出
    formatted = f"{full_domain:<30} {record_type:<8} {ttl:<6} {value}"
    
    if status == 'DISABLE':
        formatted += " [已禁用]"
    
    # 添加优先级（MX记录）
    if record.get('Priority') and record_type == 'MX':
        formatted = formatted.replace(value, f"{record['Priority']} {value}")
    
    return formatted


def format_dns_records_table(records: List[Dict[str, Any]]) -> str:
    """
    将DNS记录列表格式化为表格
    
    Args:
        records: DNS记录列表
        
    Returns:
        格式化的表格字符串
    """
    if not records:
        return "没有找到DNS记录"
    
    lines = [
        "DNS记录列表",
        "=" * 80,
        f"{'域名':<30} {'类型':<8} {'TTL':<6} 记录值",
        "-" * 80
    ]
    
    for record in records:
        lines.append(format_dns_record(record))
    
    lines.append("-" * 80)
    lines.append(f"总计: {len(records)} 条记录")
    
    return "\n".join(lines)


def format_domain_list(domains: List[Dict[str, Any]]) -> str:
    """
    格式化域名列表
    
    Args:
        domains: 域名列表
        
    Returns:
        格式化的域名列表字符串
    """
    if not domains:
        return "没有找到域名"
    
    lines = [
        "域名列表",
        "=" * 60,
        f"{'域名':<30} {'域名ID':<20} 创建时间",
        "-" * 60
    ]
    
    for domain in domains:
        domain_name = domain.get('DomainName', 'N/A')
        domain_id = domain.get('DomainId', 'N/A')
        create_time = domain.get('CreateTime', 'N/A')
        
        lines.append(f"{domain_name:<30} {domain_id:<20} {create_time}")
    
    lines.append("-" * 60)
    lines.append(f"总计: {len(domains)} 个域名")
    
    return "\n".join(lines)


def parse_record_input(input_str: str) -> Dict[str, Any]:
    """
    解析记录输入字符串
    
    Args:
        input_str: 输入字符串，格式如 "www A 1.2.3.4" 或 "@ MX 10 mail.example.com"
        
    Returns:
        解析后的记录信息
    """
    parts = input_str.strip().split()
    
    if len(parts) < 3:
        raise ValueError("输入格式错误，至少需要：主机记录 类型 值")
    
    record = {
        "rr": parts[0],
        "type": parts[1].upper(),
        "value": parts[2]
    }
    
    # 处理MX记录的优先级
    if record["type"] == "MX" and len(parts) >= 4:
        try:
            priority = int(parts[2])
            record["priority"] = priority
            record["value"] = parts[3]
        except ValueError:
            # 如果第三个参数不是数字，按普通格式处理
            pass
    
    # 处理多个值（如SRV记录）
    if len(parts) > 3 and record["type"] != "MX":
        record["value"] = " ".join(parts[2:])
    
    return record


def validate_ip_address(ip: str, version: int = 4) -> Tuple[bool, str]:
    """
    验证IP地址
    
    Args:
        ip: IP地址字符串
        version: IP版本（4或6）
        
    Returns:
        (是否有效, 错误信息)
    """
    if version == 4:
        # IPv4验证
        pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(pattern, ip):
            return False, "无效的IPv4地址格式"
        
        # 检查保留地址
        parts = [int(x) for x in ip.split('.')]
        
        # 私有地址范围
        if (parts[0] == 10 or 
            (parts[0] == 172 and 16 <= parts[1] <= 31) or
            (parts[0] == 192 and parts[1] == 168)):
            return True, "警告：这是私有IP地址"
        
        # 环回地址
        if parts[0] == 127:
            return False, "环回地址不能用于DNS记录"
        
        # 多播地址
        if 224 <= parts[0] <= 239:
            return False, "多播地址不能用于DNS记录"
        
    elif version == 6:
        # IPv6验证（简化版）
        pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::[0-9a-fA-F]{1,4}$'
        if not re.match(pattern, ip.replace('::', ':')):
            # 支持压缩格式
            if '::' in ip:
                parts = ip.split('::')
                if len(parts) != 2:
                    return False, "无效的IPv6地址格式"
            else:
                return False, "无效的IPv6地址格式"
    
    return True, ""


def calculate_ttl_suggestion(record_type: str, use_case: str = "general") -> int:
    """
    根据记录类型和使用场景建议TTL值
    
    Args:
        record_type: 记录类型
        use_case: 使用场景 (general, high_availability, testing, development)
        
    Returns:
        建议的TTL值（秒）
    """
    base_ttls = {
        "A": 3600,      # 1小时
        "AAAA": 3600,   # 1小时
        "CNAME": 1800,  # 30分钟
        "MX": 7200,     # 2小时
        "TXT": 3600,    # 1小时
        "NS": 86400,    # 24小时
        "SRV": 1800,    # 30分钟
        "CAA": 21600    # 6小时
    }
    
    base_ttl = base_ttls.get(record_type.upper(), 3600)
    
    # 根据使用场景调整
    multipliers = {
        "high_availability": 0.5,  # 高可用场景，缩短TTL
        "testing": 0.1,           # 测试场景，非常短的TTL
        "development": 0.05,      # 开发场景，极短TTL
        "general": 1.0            # 一般场景
    }
    
    multiplier = multipliers.get(use_case, 1.0)
    suggested_ttl = int(base_ttl * multiplier)
    
    # 确保TTL在合理范围内
    return max(60, min(suggested_ttl, 86400))


def format_operation_result(result: Dict[str, Any], operation: str) -> str:
    """
    格式化操作结果
    
    Args:
        result: 操作结果字典
        operation: 操作名称
        
    Returns:
        格式化的结果字符串
    """
    if result.get("success"):
        lines = [f"✅ {operation}操作成功"]
        
        if result.get("record_id"):
            lines.append(f"记录ID: {result['record_id']}")
        
        if result.get("message"):
            lines.append(f"详情: {result['message']}")
            
        return "\n".join(lines)
    else:
        lines = [f"❌ {operation}操作失败"]
        
        if result.get("error"):
            lines.append(f"错误: {result['error']}")
            
        if result.get("message"):
            lines.append(f"详情: {result['message']}")
            
        return "\n".join(lines)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def mask_sensitive_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    遮盖敏感信息
    
    Args:
        data: 原始数据
        
    Returns:
        遮盖敏感信息后的数据
    """
    sensitive_keys = ['access_key_id', 'access_key_secret', 'password', 'token', 'secret']
    
    def mask_value(key: str, value: Any) -> Any:
        if isinstance(value, str) and any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            if len(value) <= 8:
                return "***"
            else:
                return value[:4] + "*" * (len(value) - 8) + value[-4:]
        elif isinstance(value, dict):
            return {k: mask_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_value(key, item) for item in value]
        else:
            return value
    
    return {k: mask_value(k, v) for k, v in data.items()}


def create_backup_filename(original_path: str, suffix: str = "backup") -> str:
    """
    创建备份文件名
    
    Args:
        original_path: 原始文件路径
        suffix: 备份后缀
        
    Returns:
        备份文件路径
    """
    path = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return str(path.parent / f"{path.stem}_{suffix}_{timestamp}{path.suffix}")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    重试装饰器，支持指数退避
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间
        max_delay: 最大延迟时间
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if asyncio.iscoroutinefunction(func):
                        await asyncio.sleep(delay)
                    else:
                        import time
                        time.sleep(delay)
            
            raise last_exception
        
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    import time
                    time.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def check_prerequisites() -> Dict[str, Any]:
    """
    检查系统先决条件
    
    Returns:
        检查结果
    """
    result = {
        "all_good": True,
        "openssl": False,
        "certbot": False,
        "python_version": True,
        "required_packages": {},
        "warnings": []
    }
    
    # 检查Python版本
    import sys
    if sys.version_info < (3, 10):
        result["python_version"] = False
        result["all_good"] = False
        result["warnings"].append(f"Python版本过低: {sys.version}，建议使用3.10+")
    
    # 检查openssl
    import shutil
    if shutil.which("openssl"):
        result["openssl"] = True
    else:
        result["warnings"].append("未找到openssl命令，证书功能可能受限")
    
    # 检查certbot
    if shutil.which("certbot"):
        result["certbot"] = True
    else:
        result["warnings"].append("未找到certbot命令，SSL证书自动更新功能不可用")
    
    # 检查必需包
    required_packages = [
        "alibabacloud_alidns20150109",
        "alibabacloud_tea_openapi", 
        "httpx",
        "fastmcp"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            result["required_packages"][package] = True
        except ImportError:
            result["required_packages"][package] = False
            result["all_good"] = False
            result["warnings"].append(f"缺少必需包: {package}")
    
    return result
