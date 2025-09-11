#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP服务使用示例

展示如何使用各种DNS管理功能的完整示例。
注意：这些示例需要有效的阿里云API密钥才能运行。
"""

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

def check_environment():
    """检查环境配置"""
    print("=== 环境配置检查 ===")
    # 检查环境变量
    is_valid, env_result = validate_environment()
    print(f"环境变量验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    if not is_valid:
        print("缺少以下环境变量:")
        for var in env_result.get("missing_required", []):
            print(f"  - {var}")
        return False
    
    # 检查系统信息
    sys_info = get_system_info()
    print(f"Python版本: {sys_info['python_version'].split()[0]}")
    print(f"操作系统: {sys_info['platform']}")
    
    # 检查先决条件
    prereq = check_prerequisites()
    print(f"系统先决条件: {'✅ 满足' if prereq['all_good'] else '⚠️ 部分缺失'}")
    
    if prereq['warnings']:
        print("警告:")
        for warning in prereq['warnings']:
            print(f"  - {warning}")
    
    return is_valid


def example_domain_operations():
    """域名操作示例"""
    print("\n=== 域名操作示例 ===")
    try:
        # 获取域名列表
        print("\n1. 查询域名列表...")
        domains = describe_domains(page_size=5)
        
        if isinstance(domains, dict) and "error" in domains:
            print(f"❌ 查询失败: {domains['error']}")
            return
        
        print(format_domain_list(domains))
        
        # 如果有域名，查询第一个域名的DNS记录
        if domains:
            domain_name = domains[0]['DomainName']
            print(f"\n2. 查询域名 '{domain_name}' 的DNS记录...")
            
            records = describe_domain_records(domain_name, page_size=10)
            
            if isinstance(records, dict) and "error" in records:
                print(f"❌ 查询失败: {records['error']}")
            else:
                print(format_dns_records_table(records))
        else:
            print("没有找到域名")
            
    except Exception as e:
        print(f"❌ 域名操作示例执行失败: {e}")


def example_dns_record_management():
    """DNS记录管理示例"""
    print("\n=== DNS记录管理示例 ===")
    
    # 注意：这个示例需要一个真实的域名才能运行
    # 请将 'your-domain.com' 替换为您实际拥有的域名
    
    test_domain = "your-domain.com"  # 请替换为您的域名
    print(f"\n注意: 请将 '{test_domain}' 替换为您实际拥有的域名")
    print("此示例展示DNS记录管理的基本流程，但需要真实域名才能执行")
    
    # 示例代码（注释掉以避免意外执行）
    example_code = """
    from aliyun_dns_mcp.tools import (
        add_domain_record, 
        update_domain_record, 
        delete_domain_record,
        set_domain_record_status
    )
    
    # 1. 创建A记录
    print("创建A记录...")
    result = add_domain_record(
        domain_name="your-domain.com",
        rr="test",
        record_type="A",
        value="1.2.3.4",
        ttl=600
    )
    print(f"结果: {result}")
    
    if result.get('success'):
        record_id = result['record_id']
        
        # 2. 更新记录
        print("\\n更新记录...")
        update_result = update_domain_record(
            record_id=record_id,
            rr="test",
            record_type="A",
            value="2.3.4.5",
            ttl=300
        )
        print(f"结果: {update_result}")
        
        # 3. 禁用记录
        print("\\n禁用记录...")
        disable_result = set_domain_record_status(record_id, "DISABLE")
        print(f"结果: {disable_result}")
        
        # 4. 启用记录
        print("\\n启用记录...")
        enable_result = set_domain_record_status(record_id, "ENABLE")
        print(f"结果: {enable_result}")
        
        # 5. 删除记录
        print("\\n删除记录...")
        delete_result = delete_domain_record(record_id)
        print(f"结果: {delete_result}")
    """
    
    print("\n示例代码:")
    print(example_code)


def example_dynamic_ip():
    """动态IP更新示例"""
    print("\n=== 动态IP更新示例 ===")
    # 注意：这需要真实的域名和子域名
    test_domain = "your-domain.com"
    test_subdomain = "home"
    
    print(f"\n注意: 请将 '{test_domain}' 替换为您实际拥有的域名")
    print("此示例展示动态IP更新的基本流程")
    
    example_code = """
    # 检查并更新动态IP
    result = dynamic_ip_updater(
        domain_name="your-domain.com",
        rr="home",  # 子域名，如 home.your-domain.com
        record_type="A",
        dns_ttl=300,  # 动态IP建议使用较短TTL
        max_retries=3,
        retry_delay=5,
        run_once=True  # 只运行一次检查
    )
    
    if result.get('success'):
        if result.get('updated'):
            print("✅ IP地址已更新")
        else:
            print("ℹ️ IP地址未变化，无需更新")
    else:
        print(f"❌ 更新失败: {result.get('error')}")
    """
    
    print("\n示例代码:")
    print(example_code)


def example_ssl_certificates():
    """SSL证书管理示例"""
    print("\n=== SSL证书管理示例 ===")
    
    print("\n注意: SSL证书管理需要:")
    print("1. 真实的域名（DNS解析指向您的服务器）")
    print("2. 安装了certbot")
    print("3. 服务器具有公网访问权限")
    print("4. 适当的文件系统权限")
    
    example_code = """
    from aliyun_dns_mcp.tools import ssl_cert_updater
    
    # 为单个域名申请证书（测试环境）
    result = ssl_cert_updater(
        domains=["example.com"],
        email="admin@example.com",
        staging=True  # 使用Let's Encrypt测试环境
    )
    
    # 为多个域名申请证书（生产环境）
    result = ssl_cert_updater(
        domains=["example.com", "www.example.com", "api.example.com"],
        email="admin@example.com",
        cert_dir="/etc/ssl/certs",
        private_key_dir="/etc/ssl/private",
        staging=False  # 生产环境
    )
    
    if result.get('success'):
        print("✅ SSL证书管理成功")
        print(f"处理的域名: {', '.join(result.get('domains', []))}")
    else:
        print(f"❌ SSL证书管理失败: {result.get('error')}")
    """
    
    print("\n示例代码:")
    print(example_code)


def example_prompts_and_guides():
    """提示和指导示例"""
    print("\n=== 提示和指导示例 ===")
    # 中文指导
    print("\n1. 中文DNS管理指导:")
    guide = chinese_dns_management_guide("网站部署DNS配置")
    print(guide[:500] + "..." if len(guide) > 500 else guide)
    
    # 故障排除指导
    print("\n2. 认证问题故障排除:")
    troubleshooting = dns_troubleshooting_guide(
        "authentication", 
        "InvalidAccessKeyId.NotFound"
    )
    print(troubleshooting[:500] + "..." if len(troubleshooting) > 500 else troubleshooting)
    
    # 配置模板
    print("\n3. 网站DNS配置模板:")
    template = dns_configuration_template("example.com", "website")
    print(template[:500] + "..." if len(template) > 500 else template)


def example_resources():
    """资源管理示例"""
    print("\n=== 资源管理示例 ===")
    # 读取证书目录
    print("\n1. 读取当前目录结构:")
    try:
        directory_info = cert_directory_reader(".")
        print(directory_info[:500] + "..." if len(directory_info) > 500 else directory_info)
    except Exception as e:
        print(f"❌ 读取目录失败: {e}")
    
    # 列出证书文件
    print("\n2. 列出系统证书:")
    try:
        cert_list = list_all_certificates()
        print(cert_list[:500] + "..." if len(cert_list) > 500 else cert_list)
    except Exception as e:
        print(f"❌ 列出证书失败: {e}")


def main():
    """主函数"""
    print("阿里云DNS MCP服务使用示例")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请设置正确的环境变量后重试")
        print("\n需要设置:")
        print("export ALIBABA_CLOUD_ACCESS_KEY_ID='your_access_key_id'")
        print("export ALIBABA_CLOUD_ACCESS_KEY_SECRET='your_access_key_secret'")
        return
    
    # 运行示例
    try:
        example_domain_operations()
        example_dns_record_management()
        example_dynamic_ip()
        example_ssl_certificates()
        example_prompts_and_guides()
        example_resources()
        
        print("\n=== 示例完成 ===")
        print("✅ 所有示例已执行完毕")
        print("\n提示:")
        print("- 将示例中的 'your-domain.com' 替换为您的真实域名")
        print("- 在测试环境中先验证功能后再在生产环境使用")
        print("- 查看README.md获取更多详细信息")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
