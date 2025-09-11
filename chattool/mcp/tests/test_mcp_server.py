#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP服务器测试

测试MCP服务器的基本功能，包括工具、提示和资源。
"""

import os
import sys
import pytest
import json
import asyncio
from pathlib import Path
from chattool.mcp.aliyun import (
    validate_environment,
    get_system_info,
    config_manager,
    format_dns_record,
    format_dns_records_table,
    validate_ip_address,
    check_prerequisites,
    chinese_dns_management_guide,
    english_dns_management_guide,
    japanese_dns_management_guide,
    dns_troubleshooting_guide,
    dns_configuration_template,
    list_all_certificates,
    cert_directory_reader,
)

class TestEnvironment:
    """环境配置测试"""
    
    def test_environment_validation(self):
        """测试环境变量验证"""
        result = validate_environment()
        assert isinstance(result, dict)
        assert "valid" in result
        assert "missing_required" in result
        assert "present_required" in result
    
    def test_system_info(self):
        """测试系统信息获取"""
        info = get_system_info()
        assert isinstance(info, dict)
        assert "python_version" in info
        assert "platform" in info
        assert "working_directory" in info

class TestUtils:
    """工具函数测试"""
    
    def test_domain_validation(self):
        """测试域名验证"""
        # 有效域名
        valid, error = config_manager.validate_domain_name("example.com")
        assert valid
        
        valid, error = config_manager.validate_domain_name("sub.example.com")
        assert valid
        
        # 无效域名
        valid, error = config_manager.validate_domain_name("")
        assert not valid
        
        valid, error = config_manager.validate_domain_name(".example.com")
        assert not valid
        
        valid, error = config_manager.validate_domain_name("example.")
        assert not valid
    
    def test_record_type_validation(self):
        """测试记录类型验证"""
        # 有效记录类型
        valid, error = config_manager.validate_record_type("A")
        assert valid
        
        valid, error = config_manager.validate_record_type("CNAME")
        assert valid
        
        # 无效记录类型
        valid, error = config_manager.validate_record_type("")
        assert not valid
        
        valid, error = config_manager.validate_record_type("INVALID")
        assert not valid
    
    def test_ip_validation(self):
        """测试IP地址验证"""
        # 有效IPv4
        valid, error = validate_ip_address("192.168.1.1")
        assert valid
        
        valid, error = validate_ip_address("8.8.8.8")
        assert valid
        
        # 无效IPv4
        valid, error = validate_ip_address("256.1.1.1")
        assert not valid
        
        valid, error = validate_ip_address("127.0.0.1")
        assert not valid  # 环回地址
    
    def test_ttl_validation(self):
        """测试TTL验证"""
        # 有效TTL
        valid, error = config_manager.validate_ttl(300)
        assert valid
        
        valid, error = config_manager.validate_ttl(3600)
        assert valid
        
        # 无效TTL
        valid, error = config_manager.validate_ttl(0)
        assert not valid
        
        valid, error = config_manager.validate_ttl(-1)
        assert not valid
    
    def test_format_functions(self):
        """测试格式化函数"""
        # 测试单条记录格式化
        record = {
            'DomainName': 'example.com',
            'RR': 'www',
            'Type': 'A',
            'Value': '1.2.3.4',
            'TTL': 600,
            'Status': 'ENABLE'
        }
        formatted = format_dns_record(record)
        assert isinstance(formatted, str)
        assert 'www.example.com' in formatted
        assert '1.2.3.4' in formatted
        
        # 测试记录列表格式化
        records = [record]
        table = format_dns_records_table(records)
        assert isinstance(table, str)
        assert 'DNS记录列表' in table
        assert '总计: 1 条记录' in table
        
        # 测试空列表
        empty_table = format_dns_records_table([])
        assert '没有找到DNS记录' in empty_table


class TestPrompts:
    """提示功能测试"""
    
    def test_chinese_guide(self):
        """测试中文指导"""
        guide = chinese_dns_management_guide("测试上下文")
        assert isinstance(guide, str)
        assert "阿里云DNS管理指导" in guide
        assert "测试上下文" in guide
    
    def test_english_guide(self):
        """测试英文指导"""
        guide = english_dns_management_guide("Test context")
        assert isinstance(guide, str)
        assert "Aliyun DNS Management Guide" in guide
        assert "Test context" in guide
    
    def test_japanese_guide(self):
        """测试日文指导"""
        guide = japanese_dns_management_guide("テストコンテキスト")
        assert isinstance(guide, str)
        assert "Aliyun DNS管理ガイド" in guide
        assert "テストコンテキスト" in guide
    
    def test_troubleshooting_guide(self):
        """测试故障排除指导"""        
        guide = dns_troubleshooting_guide("authentication", "Invalid key")
        assert isinstance(guide, str)
        assert "认证问题排除" in guide
        assert "Invalid key" in guide
    
    def test_configuration_template(self):
        """测试配置模板"""
        template = dns_configuration_template("example.com", "website")
        assert isinstance(template, str)
        assert "网站DNS配置模板" in template
        assert "example.com" in template


class TestResources:
    """资源管理测试"""
    
    def test_cert_directory_reader(self):
        """测试证书目录读取"""
        # 测试读取当前目录
        result = cert_directory_reader(".")
        assert isinstance(result, str)
        
        # 解析JSON结果
        import json
        try:
            data = json.loads(result)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("返回的不是有效的JSON")
    
    def test_list_certificates(self):
        """测试证书列表"""
        result = list_all_certificates()
        assert isinstance(result, str)
        
        # 解析JSON结果
        try:
            data = json.loads(result)
            assert isinstance(data, dict)
            assert "total_count" in data
            assert "certificates" in data
        except json.JSONDecodeError:
            pytest.fail("返回的不是有效的JSON")


class TestPrerequisites:
    """先决条件测试"""
    
    def test_check_prerequisites(self):
        """测试先决条件检查"""
        result = check_prerequisites()
        assert isinstance(result, dict)
        assert "all_good" in result
        assert "python_version" in result
        assert "required_packages" in result
        assert "warnings" in result
    
    def test_python_version(self):
        """测试Python版本检查"""
        # 确保Python版本符合要求
        assert sys.version_info >= (3, 10), f"Python版本过低: {sys.version}"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
