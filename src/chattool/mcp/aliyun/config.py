#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP配置管理

提供环境变量验证、配置检查和错误处理功能。
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.required_env_vars = [
            'ALIBABA_CLOUD_ACCESS_KEY_ID',
            'ALIBABA_CLOUD_ACCESS_KEY_SECRET'
        ]
        self.optional_env_vars = {
            'ALIBABA_CLOUD_ENDPOINT': 'alidns.cn-hangzhou.aliyuncs.com',
            'CERT_DIR': '/etc/ssl/certs',
            'PRIVATE_KEY_DIR': '/etc/ssl/private',
            'LOG_LEVEL': 'INFO'
        }
    
    def validate_environment(self) -> Tuple[bool, Dict[str, Any]]:
        """
        验证环境变量配置
        
        Returns:
            (是否有效, 验证结果详情)
        """
        result = {
            "valid": True,
            "missing_required": [],
            "present_required": [],
            "optional_vars": {},
            "recommendations": []
        }
        
        # 检查必需的环境变量
        for var in self.required_env_vars:
            value = os.getenv(var)
            if value:
                result["present_required"].append(var)
                # 检查密钥格式（基本验证）
                if var == 'ALIBABA_CLOUD_ACCESS_KEY_ID' and len(value) < 10:
                    result["recommendations"].append(f"{var} 似乎太短，请确认是否正确")
                elif var == 'ALIBABA_CLOUD_ACCESS_KEY_SECRET' and len(value) < 20:
                    result["recommendations"].append(f"{var} 似乎太短，请确认是否正确")
            else:
                result["missing_required"].append(var)
                result["valid"] = False
        
        # 检查可选环境变量
        for var, default in self.optional_env_vars.items():
            value = os.getenv(var, default)
            result["optional_vars"][var] = value
        
        # 添加安全建议
        if result["valid"]:
            result["recommendations"].extend([
                "建议定期轮换API密钥",
                "确保不要在代码中硬编码密钥",
                "生产环境请使用适当的权限管理"
            ])
        
        return result["valid"], result
    
    def get_dns_client_config(self) -> Dict[str, Any]:
        """
        获取DNS客户端配置
        
        Returns:
            DNS客户端配置
        """
        return {
            "access_key_id": os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
            "access_key_secret": os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
            "endpoint": os.getenv('ALIBABA_CLOUD_ENDPOINT', 'alidns.cn-hangzhou.aliyuncs.com')
        }
    
    def get_certificate_config(self) -> Dict[str, Any]:
        """
        获取证书管理配置
        
        Returns:
            证书管理配置
        """
        return {
            "cert_dir": os.getenv('CERT_DIR', '/etc/ssl/certs'),
            "private_key_dir": os.getenv('PRIVATE_KEY_DIR', '/etc/ssl/private'),
            "letsencrypt_dir": '/etc/letsencrypt'
        }
    
    def setup_logging(self) -> logging.Logger:
        """
        设置日志配置
        
        Returns:
            配置好的日志记录器
        """
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # 创建日志记录器
        logger = logging.getLogger('aliyun_dns_mcp')
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # 清除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        
        return logger
    
    def validate_domain_name(self, domain: str) -> Tuple[bool, str]:
        """
        验证域名格式
        
        Args:
            domain: 域名
            
        Returns:
            (是否有效, 错误信息)
        """
        if not domain:
            return False, "域名不能为空"
        
        # 基本格式检查
        if not domain.replace('-', '').replace('.', '').replace('_', '').isalnum():
            return False, "域名包含非法字符"
        
        if domain.startswith('.') or domain.endswith('.'):
            return False, "域名不能以点开始或结束"
        
        if '..' in domain:
            return False, "域名不能包含连续的点"
        
        parts = domain.split('.')
        if len(parts) < 2:
            return False, "域名至少需要包含一个点"
        
        for part in parts:
            if len(part) == 0:
                return False, "域名部分不能为空"
            if len(part) > 63:
                return False, "域名部分长度不能超过63个字符"
        
        if len(domain) > 253:
            return False, "域名总长度不能超过253个字符"
        
        return True, ""
    
    def validate_record_type(self, record_type: str) -> Tuple[bool, str]:
        """
        验证DNS记录类型
        
        Args:
            record_type: 记录类型
            
        Returns:
            (是否有效, 错误信息)
        """
        valid_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA', 'PTR']
        
        if not record_type:
            return False, "记录类型不能为空"
        
        if record_type.upper() not in valid_types:
            return False, f"不支持的记录类型: {record_type}，支持的类型: {', '.join(valid_types)}"
        
        return True, ""
    
    def validate_record_value(self, record_type: str, value: str) -> Tuple[bool, str]:
        """
        验证DNS记录值
        
        Args:
            record_type: 记录类型
            value: 记录值
            
        Returns:
            (是否有效, 错误信息)
        """
        if not value:
            return False, "记录值不能为空"
        
        record_type = record_type.upper()
        
        if record_type == 'A':
            # IPv4地址验证
            parts = value.split('.')
            if len(parts) != 4:
                return False, "A记录值必须是有效的IPv4地址"
            try:
                for part in parts:
                    num = int(part)
                    if num < 0 or num > 255:
                        return False, "A记录值必须是有效的IPv4地址"
            except ValueError:
                return False, "A记录值必须是有效的IPv4地址"
        
        elif record_type == 'AAAA':
            # IPv6地址验证（简单检查）
            if ':' not in value:
                return False, "AAAA记录值必须是有效的IPv6地址"
        
        elif record_type == 'CNAME':
            # CNAME值验证（必须是域名）
            is_valid, error = self.validate_domain_name(value.rstrip('.'))
            if not is_valid:
                return False, f"CNAME记录值必须是有效域名: {error}"
        
        elif record_type == 'MX':
            # MX记录值验证（可能包含优先级）
            parts = value.split()
            if len(parts) == 2:
                try:
                    priority = int(parts[0])
                    if priority < 0 or priority > 65535:
                        return False, "MX记录优先级必须在0-65535之间"
                    domain = parts[1]
                except ValueError:
                    domain = value
            else:
                domain = value
            
            is_valid, error = self.validate_domain_name(domain.rstrip('.'))
            if not is_valid:
                return False, f"MX记录值必须是有效域名: {error}"
        
        # 其他记录类型的基本验证
        elif record_type in ['TXT', 'NS', 'SRV', 'CAA', 'PTR']:
            if len(value) > 512:
                return False, f"{record_type}记录值长度不能超过512个字符"
        
        return True, ""
    
    def validate_ttl(self, ttl: int) -> Tuple[bool, str]:
        """
        验证TTL值
        
        Args:
            ttl: TTL值
            
        Returns:
            (是否有效, 错误信息)
        """
        if ttl < 1:
            return False, "TTL值必须大于0"
        
        if ttl > 86400:  # 24小时
            return False, "TTL值不应超过86400秒（24小时）"
        
        # 建议值范围
        if ttl < 60:
            return True, "警告：TTL值过小可能导致DNS查询频繁"
        
        return True, ""


# 全局配置管理器实例
config_manager = ConfigManager()


def validate_environment() -> Tuple[bool, Dict[str, Any]]:
    """
    验证环境配置
    
    Returns:
        (是否有效, 环境验证结果)
    """
    return config_manager.validate_environment()


def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息
    """
    return {
        "python_version": os.sys.version,
        "platform": os.sys.platform,
        "working_directory": os.getcwd(),
        "user": os.getenv('USER', 'unknown'),
        "home": os.getenv('HOME', 'unknown'),
        "environment_variables": {
            k: "***" if "KEY" in k or "SECRET" in k or "PASSWORD" in k else v
            for k, v in os.environ.items()
            if k.startswith('ALIBABA_') or k.startswith('CERT_') or k in ['LOG_LEVEL']
        }
    }
