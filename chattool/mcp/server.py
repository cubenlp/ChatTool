#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP服务器

基于ChatTool项目和FastMCP框架的完整阿里云DNS管理服务。
提供DNS记录管理、动态IP更新、SSL证书管理等功能。
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
import click

from chattool.mcp.aliyun.tools import (
    describe_domains,
    describe_domain_records,
    add_domain_record,
    update_domain_record,
    delete_domain_record,
    set_domain_record_status,
    dynamic_ip_updater,
    ssl_cert_updater
)
from chattool.mcp.aliyun.prompts import (
    chinese_dns_management_guide,
    english_dns_management_guide,
    japanese_dns_management_guide,
    dns_troubleshooting_guide,
    dns_configuration_template
)
from chattool.mcp.aliyun.resources import (
    cert_directory_reader,
    cert_file_content,
    cert_directory_writer,
    list_all_certificates
)
from chattool.mcp.aliyun.config import (
    validate_environment,
    get_system_info
)
from chattool.mcp.aliyun.utils import (
    format_dns_records_table,
    format_domain_list,
    format_operation_result,
    check_prerequisites
)

# 创建MCP服务实例
mcp = FastMCP("阿里云DNS管理服务")

# ============ MCP工具函数定义 ============

@mcp.tool
def list_domains(page_number: int = 1, page_size: int = 20) -> str:
    """查看域名列表
    
    查询阿里云账户下的所有域名，支持分页查询。
    
    Args:
        page_number: 页码，从1开始，默认为1
        page_size: 每页记录数，默认为20，最大值500
        
    Returns:
        格式化的域名列表
    """
    try:
        domains = describe_domains(page_number=page_number, page_size=page_size)
        
        if isinstance(domains, dict) and "error" in domains:
            return f"❌ 查询域名失败: {domains['error']}"
        
        return format_domain_list(domains)
    except Exception as e:
        return f"❌ 查询域名时发生异常: {str(e)}"


@mcp.tool
def list_domain_records(domain_name: str, page_number: int = 1, page_size: int = 20) -> str:
    """查看域名解析记录
    
    查询指定域名的所有DNS解析记录，支持分页查询。
    
    Args:
        domain_name: 域名，如 example.com
        page_number: 页码，从1开始，默认为1  
        page_size: 每页记录数，默认为20，最大值500
        
    Returns:
        格式化的DNS记录列表
    """
    try:
        if not domain_name:
            return "❌ 域名不能为空"
            
        records = describe_domain_records(
            domain_name=domain_name,
            page_number=page_number, 
            page_size=page_size
        )
        
        if isinstance(records, dict) and "error" in records:
            return f"❌ 查询DNS记录失败: {records['error']}"
        
        return format_dns_records_table(records)
    except Exception as e:
        return f"❌ 查询DNS记录时发生异常: {str(e)}"


@mcp.tool  
def create_domain_record(domain_name: str, rr: str, record_type: str, value: str,
                        ttl: int = 600, line: str = "default", priority: Optional[int] = None) -> str:
    """添加域名解析记录
    
    为指定域名创建新的DNS解析记录，支持A、AAAA、CNAME、MX、TXT等记录类型。
    
    Args:
        domain_name: 域名，如 example.com
        rr: 主机记录，如 www、@、*
        record_type: 记录类型，如 A、AAAA、CNAME、MX、TXT、NS、SRV、CAA
        value: 记录值，如IP地址、域名或文本
        ttl: 生存时间（秒），默认600秒
        line: 解析线路，默认 'default'  
        priority: MX记录优先级（仅MX记录需要）
        
    Returns:
        操作结果说明
    """
    try:
        result = add_domain_record(
            domain_name=domain_name,
            rr=rr,
            record_type=record_type,
            value=value,
            ttl=ttl,
            line=line,
            priority=priority
        )
        
        return format_operation_result(result, "创建DNS记录")
    except Exception as e:
        return f"❌ 创建DNS记录时发生异常: {str(e)}"


@mcp.tool
def modify_domain_record(record_id: str, rr: str, record_type: str, value: str,
                        ttl: int = 600, line: str = "default", priority: Optional[int] = None) -> str:
    """更新域名解析记录
    
    修改已存在的DNS解析记录的内容。
    
    Args:
        record_id: 解析记录的ID
        rr: 主机记录，如 www、@、*
        record_type: 记录类型，如 A、AAAA、CNAME、MX、TXT、NS、SRV、CAA
        value: 记录值，如IP地址、域名或文本
        ttl: 生存时间（秒），默认600秒
        line: 解析线路，默认 'default'
        priority: MX记录优先级（仅MX记录需要）
        
    Returns:
        操作结果说明
    """
    try:
        result = update_domain_record(
            record_id=record_id,
            rr=rr,
            record_type=record_type,
            value=value,
            ttl=ttl,
            line=line,
            priority=priority
        )
        
        return format_operation_result(result, "更新DNS记录")
    except Exception as e:
        return f"❌ 更新DNS记录时发生异常: {str(e)}"


@mcp.tool
def remove_domain_record(record_id: str) -> str:
    """删除域名解析记录
    
    删除指定的DNS解析记录。
    
    Args:
        record_id: 解析记录的ID
        
    Returns:
        操作结果说明
    """
    try:
        result = delete_domain_record(record_id=record_id)
        return format_operation_result(result, "删除DNS记录")
    except Exception as e:
        return f"❌ 删除DNS记录时发生异常: {str(e)}"


@mcp.tool
def toggle_record_status(record_id: str, status: str) -> str:
    """设置域名解析记录状态
    
    启用或禁用DNS解析记录。
    
    Args:
        record_id: 解析记录的ID
        status: 状态值，ENABLE（启用）或 DISABLE（禁用）
        
    Returns:
        操作结果说明
    """
    try:
        if status not in ["ENABLE", "DISABLE"]:
            return "❌ 状态值必须为 ENABLE 或 DISABLE"
            
        result = set_domain_record_status(record_id=record_id, status=status)
        return format_operation_result(result, "设置DNS记录状态")
    except Exception as e:
        return f"❌ 设置DNS记录状态时发生异常: {str(e)}"


@mcp.tool
def update_dynamic_ip(domain_name: str, rr: str, record_type: str = "A",
                     dns_ttl: int = 600, max_retries: int = 3, retry_delay: int = 5) -> str:
    """动态IP监控和DNS自动更新
    
    检查当前公网IP地址，如果与DNS记录不一致则自动更新。适用于动态IP环境。
    
    Args:
        domain_name: 域名，如 example.com
        rr: 子域名记录，如 home、ddns
        record_type: DNS记录类型，默认为A记录
        dns_ttl: TTL值，默认600秒
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试延迟（秒），默认5秒
        
    Returns:
        更新结果说明
    """
    try:
        result = dynamic_ip_updater(
            domain_name=domain_name,
            rr=rr,
            record_type=record_type,
            dns_ttl=dns_ttl,
            max_retries=max_retries,
            retry_delay=retry_delay,
            run_once=True
        )
        
        if result.get("success"):
            if result.get("updated"):
                return f"✅ 动态IP更新成功: {result.get('message', '')}"
            else:
                return f"ℹ️ IP地址未变化，无需更新: {result.get('message', '')}"
        else:
            return f"❌ 动态IP更新失败: {result.get('error', '')}"
            
    except Exception as e:
        return f"❌ 动态IP更新时发生异常: {str(e)}"


@mcp.tool
def manage_ssl_certificates(domains: List[str], email: str, cert_dir: str = "/etc/ssl/certs",
                          private_key_dir: str = "/etc/ssl/private", staging: bool = False) -> str:
    """SSL证书自动更新和DNS挑战管理
    
    使用Let's Encrypt自动申请和更新SSL证书，通过DNS-01挑战验证域名所有权。
    
    Args:
        domains: 域名列表，如 ["example.com", "www.example.com"]
        email: Let's Encrypt账户邮箱地址
        cert_dir: 证书存储目录，默认 /etc/ssl/certs
        private_key_dir: 私钥存储目录，默认 /etc/ssl/private  
        staging: 是否使用Let's Encrypt测试环境，默认False
        
    Returns:
        证书管理结果说明
    """
    try:
        if not domains:
            return "❌ 域名列表不能为空"
            
        if not email:
            return "❌ 邮箱地址不能为空"
            
        result = ssl_cert_updater(
            domains=domains,
            email=email,
            cert_dir=cert_dir,
            private_key_dir=private_key_dir,
            staging=staging
        )
        
        if result.get("success"):
            env_info = " [测试环境]" if staging else " [生产环境]"
            domains_str = ", ".join(domains)
            return f"✅ SSL证书管理成功{env_info}\n域名: {domains_str}\n{result.get('message', '')}"
        else:
            return f"❌ SSL证书管理失败: {result.get('error', '')}"
            
    except Exception as e:
        return f"❌ SSL证书管理时发生异常: {str(e)}"


# ============ MCP提示模板定义 ============

@mcp.prompt
def aliyun_dns_guide_chinese(context: str = "阿里云DNS管理") -> str:
    """中文版阿里云DNS管理指导
    
    提供中文版的阿里云DNS管理指导，包含常见操作场景和最佳实践。
    
    Args:
        context: 上下文信息，描述当前需要指导的场景
        
    Returns:
        详细的中文DNS管理指导
    """
    return chinese_dns_management_guide(context)


@mcp.prompt  
def aliyun_dns_guide_english(context: str = "Aliyun DNS Management") -> str:
    """English Aliyun DNS Management Guide
    
    Provides English version of Aliyun DNS management guide with common scenarios and best practices.
    
    Args:
        context: Context information describing the current scenario needing guidance
        
    Returns:
        Detailed English DNS management guide
    """
    return english_dns_management_guide(context)


@mcp.prompt
def aliyun_dns_guide_japanese(context: str = "Aliyun DNS管理") -> str:
    """日本語版Aliyun DNS管理ガイド
    
    日本語版のAliyun DNS管理ガイドを提供し、一般的なシナリオとベストプラクティスを含みます。
    
    Args:
        context: ガイダンスが必要な現在のシナリオを説明するコンテキスト情報
        
    Returns:
        詳細な日本語DNS管理ガイド
    """
    return japanese_dns_management_guide(context)


@mcp.prompt
def dns_troubleshooting(issue_type: str, error_message: str = "") -> str:
    """DNS故障排除指导
    
    根据问题类型提供针对性的故障排除指导。
    
    Args:
        issue_type: 问题类型，如 authentication、dns_record、network
        error_message: 具体的错误信息
        
    Returns:
        针对性的故障排除步骤和解决方案
    """
    return dns_troubleshooting_guide(issue_type, error_message)


@mcp.prompt
def dns_config_template(domain_name: str, use_case: str = "website") -> str:
    """DNS配置模板生成器
    
    根据域名和使用场景生成DNS配置模板。
    
    Args:
        domain_name: 域名，如 example.com
        use_case: 使用场景，如 website、api、email
        
    Returns:
        针对特定场景的DNS配置模板
    """
    return dns_configuration_template(domain_name, use_case)


# ============ MCP资源定义 ============

# @mcp.resource("cert://directory")
# async def cert_directory_resource() -> str:
#     """证书目录资源
    
#     读取证书目录结构和文件信息。
    
#     Args:
#         path: 目录路径，如果为空则使用默认证书目录
        
#     Returns:
#         目录结构的JSON格式数据
#     """
#     return cert_directory_reader(path if path != "default" else None)


# @mcp.resource("cert://file")  
# async def cert_file_resource() -> str:
#     """证书文件资源
    
#     读取特定证书文件的内容和信息。
    
#     Args:
#         file_path: 证书文件路径
        
#     Returns:
#         文件内容和证书信息的JSON格式数据
#     """
#     return cert_file_content(file_path)


@mcp.resource("cert://list")
async def cert_list_resource() -> str:
    """证书列表资源
    
    列出系统中的所有证书文件。
    
    Returns:
        所有证书文件的JSON格式列表
    """
    return list_all_certificates()


@mcp.resource("system://environment")
async def system_environment_resource() -> str:
    """系统环境资源
    
    获取系统环境配置信息和验证结果。
    
    Returns:
        系统环境信息的JSON格式数据
    """
    import json
    
    env_result = validate_environment()
    sys_info = get_system_info()
    prerequisites = check_prerequisites()
    
    return json.dumps({
        "environment_validation": env_result,
        "system_info": sys_info,
        "prerequisites": prerequisites
    }, indent=2, ensure_ascii=False)


# ============ 服务器启动配置 ============

@click.command()
@click.option('--transport', 
              type=click.Choice(['stdio', 'http']), 
              default='stdio', 
              help='传输协议')
@click.option('--host', 
              default='localhost', 
              help='SSE服务器主机')
@click.option('--port', 
              type=int, 
              default=3000, 
              help='SSE服务器端口')
def main(transport, host, port):
    """阿里云DNS MCP服务器"""
    
    # 验证环境配置
    is_valid, env_result = validate_environment()
    if not is_valid:
        print("❌ 环境配置验证失败:")
        for var in env_result.get("missing_required", []):
            print(f"  缺少环境变量: {var}")
        print("\n请设置以下环境变量:")
        print("  export ALIBABA_CLOUD_ACCESS_KEY_ID='your_access_key_id'")  
        print("  export ALIBABA_CLOUD_ACCESS_KEY_SECRET='your_access_key_secret'")
        sys.exit(1)
    else:
        print("✅ 环境配置验证通过")
    
    # 检查系统先决条件
    prereq_result = check_prerequisites()
    if not prereq_result["all_good"]:
        print("⚠️  系统先决条件检查发现问题:")
        for warning in prereq_result.get("warnings", []):
            print(f"  {warning}")
        print()
    
    # 启动服务器
    print(f"🚀 启动阿里云DNS MCP服务器...")
    print(f"   传输协议: {transport}")
    
    if transport == "stdio":
        print("   模式: STDIO")
        mcp.run()
    else:
        print(f"   模式: SSE服务器 ({host}:{port})")  
        mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    main()
