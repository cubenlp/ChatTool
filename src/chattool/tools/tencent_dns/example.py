#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 DNSPod 客户端使用示例

展示如何使用 TencentDNSClient 进行域名解析记录的 CRUD 操作
"""

import os
import asyncio
from .client import TencentDNSClient
from .dynamic_ip_updater import DynamicIPUpdater
from .ssl_cert_updater import SSLCertUpdater


def basic_dns_operations():
    """基础DNS操作示例"""
    print("=== 腾讯云 DNSPod 客户端基础操作示例 ===\n")
    
    # 初始化客户端
    try:
        client = TencentDNSClient()
    except ValueError as e:
        print(f"初始化失败: {e}")
        print("请设置环境变量 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")
        return
    
    # 示例域名
    domain = "example.com"  # 请替换为您的实际域名
    
    # 1. 查看域名列表
    print("1. 查看域名列表:")
    domains = client.describe_domains()
    if domains:
        for domain_info in domains[:3]:  # 只显示前3个
            print(f"  - {domain_info['DomainName']} (ID: {domain_info['DomainId']}, 状态: {domain_info['Status']})")
    else:
        print("  没有找到域名")
    print()
    
    # 2. 查看解析记录
    print(f"2. 查看域名 {domain} 的解析记录:")
    records = client.describe_domain_records(domain)
    if records:
        for record in records[:5]:  # 只显示前5条
            print(f"  - {record['RR']}.{domain} {record['Type']} {record['Value']} (TTL: {record['TTL']})")
    else:
        print("  没有找到解析记录")
    print()
    
    # 3. 创建新的解析记录
    print("3. 创建新的解析记录:")
    record_id = client.add_domain_record(
        domain_name=domain,
        rr="test",
        type_="A",
        value="1.2.3.4",
        ttl=600,
        remark="测试记录"
    )
    if record_id:
        print(f"  创建成功，记录ID: {record_id}")
    else:
        print("  创建失败")
    print()
    
    # 4. 修改解析记录（如果上步创建成功）
    if record_id:
        print("4. 修改解析记录:")
        success = client.update_domain_record(
            record_id=record_id,
            rr="test",
            type_="A",
            value="5.6.7.8",
            domain_name=domain,
            ttl=300,
            remark="更新后的测试记录"
        )
        if success:
            print("  修改成功")
        else:
            print("  修改失败")
        print()
        
        # 5. 设置记录状态
        print("5. 设置记录状态:")
        success = client.set_domain_record_status(
            record_id=record_id,
            status="DISABLE",
            domain_name=domain
        )
        if success:
            print("  状态设置成功 (已禁用)")
        else:
            print("  状态设置失败")
        print()
        
        # 6. 删除解析记录
        print("6. 删除解析记录:")
        success = client.delete_domain_record(record_id, domain)
        if success:
            print("  删除成功")
        else:
            print("  删除失败")
        print()
    
    # 7. 使用高级封装方法
    print("7. 使用高级封装方法:")
    
    # 设置记录值（不存在则创建，存在则更新）
    success = client.set_record_value(
        domain_name=domain,
        rr="api",
        type_="A", 
        value="10.0.0.1",
        ttl=300
    )
    if success:
        print("  设置 api.example.com A 记录成功")
    else:
        print("  设置记录失败")
    
    # 删除指定记录
    success = client.delete_record_value(
        domain_name=domain,
        rr="api",
        type_="A"
    )
    if success:
        print("  删除 api.example.com A 记录成功")
    else:
        print("  删除记录失败")
    
    print("\n=== 基础操作示例完成 ===")


def batch_operations_example():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===\n")
    
    try:
        client = TencentDNSClient()
    except ValueError as e:
        print(f"初始化失败: {e}")
        return
    
    domain = "example.com"  # 请替换为您的实际域名
    
    # 批量创建记录
    records_to_create = [
        {"rr": "www", "type": "A", "value": "192.168.1.1"},
        {"rr": "mail", "type": "A", "value": "192.168.1.2"},
        {"rr": "ftp", "type": "A", "value": "192.168.1.3"},
        {"rr": "blog", "type": "CNAME", "value": "www.example.com"},
    ]
    
    created_ids = []
    for record_info in records_to_create:
        record_id = client.add_domain_record(
            domain_name=domain,
            rr=record_info["rr"],
            type_=record_info["type"],
            value=record_info["value"],
            ttl=600
        )
        if record_id:
            created_ids.append(record_id)
            print(f"创建 {record_info['rr']}.{domain} {record_info['type']} {record_info['value']} 成功")
        else:
            print(f"创建 {record_info['rr']}.{domain} 失败")
    
    print(f"\n批量创建完成，成功创建 {len(created_ids)} 条记录\n")
    
    # 批量删除记录
    print("批量删除记录:")
    for record_id in created_ids:
        success = client.delete_domain_record(record_id, domain)
        if success:
            print(f"删除记录 {record_id} 成功")
        else:
            print(f"删除记录 {record_id} 失败")
    
    print("\n=== 批量操作完成 ===")


async def dynamic_ip_example():
    """动态IP更新示例"""
    print("\n=== 动态IP更新示例 ===\n")
    
    domain = "example.com"  # 请替换为您的实际域名
    rr = "ddns"  # 要更新的子域名
    
    try:
        # 创建动态IP更新器
        updater = DynamicIPUpdater(
            domain_name=domain,
            rr=rr,
            record_type="A",
            dns_ttl=300,
            max_retries=3,
            retry_delay=5
        )
        
        print(f"开始检查和更新 {rr}.{domain} 的IP地址...")
        
        # 执行一次检查和更新
        success = await updater.run_once()
        if success:
            print("IP检查和更新完成")
        else:
            print("IP检查和更新失败")
        
    except Exception as e:
        print(f"动态IP更新失败: {e}")
    
    print("\n=== 动态IP更新示例完成 ===")


def ssl_cert_example():
    """SSL证书管理示例"""
    print("\n=== SSL证书管理示例 ===\n")
    
    domains = ["example.com", "www.example.com"]  # 请替换为您的实际域名
    email = "your@email.com"  # 请替换为您的邮箱
    
    try:
        # 创建SSL证书更新器
        updater = SSLCertUpdater(
            domains=domains,
            email=email,
            staging=True,  # 使用测试环境
            cert_dir="/tmp/certs",  # 测试目录
            private_key_dir="/tmp/private"
        )
        
        print(f"检查域名 {', '.join(domains)} 的证书状态...")
        
        # 检查是否需要更新
        if updater.needs_renewal():
            print("证书需要更新")
            # 注意：实际的证书申请需要acme.sh和DNS验证
            # 这里只是演示检查逻辑
        else:
            print("证书状态正常")
        
        # 检查证书过期时间
        expiry_date = updater.check_certificate_expiry()
        if expiry_date:
            print(f"证书过期时间: {expiry_date}")
        else:
            print("证书文件不存在")
        
    except Exception as e:
        print(f"SSL证书管理失败: {e}")
    
    print("\n=== SSL证书管理示例完成 ===")


def advanced_query_example():
    """高级查询示例"""
    print("\n=== 高级查询示例 ===\n")
    
    try:
        client = TencentDNSClient()
    except ValueError as e:
        print(f"初始化失败: {e}")
        return
    
    domain = "example.com"  # 请替换为您的实际域名
    
    # 1. 查询特定类型的记录
    print("1. 查询A记录:")
    a_records = client.describe_domain_records(
        domain_name=domain,
        record_type="A"
    )
    for record in a_records[:3]:
        print(f"  - {record['RR']}.{domain} -> {record['Value']}")
    
    # 2. 查询特定子域名的记录
    print("\n2. 查询www子域名记录:")
    www_records = client.describe_domain_records(
        domain_name=domain,
        subdomain="www"
    )
    for record in www_records:
        print(f"  - {record['RR']}.{domain} {record['Type']} {record['Value']}")
    
    # 3. 使用关键字搜索
    print("\n3. 搜索包含'mail'的记录:")
    mail_records = client.describe_domain_records(
        domain_name=domain,
        keyword="mail"
    )
    for record in mail_records:
        print(f"  - {record['RR']}.{domain} {record['Type']} {record['Value']}")
    
    # 4. 分页查询
    print("\n4. 分页查询记录:")
    paged_records = client.describe_domain_records(
        domain_name=domain,
        offset=0,
        limit=5
    )
    print(f"  查询到 {len(paged_records)} 条记录")
    
    # 5. 排序查询
    print("\n5. 按类型排序查询:")
    sorted_records = client.describe_domain_records(
        domain_name=domain,
        sort_field="type",
        sort_type="ASC",
        limit=10
    )
    for record in sorted_records:
        print(f"  - {record['Type']}: {record['RR']}.{domain} -> {record['Value']}")
    
    print("\n=== 高级查询示例完成 ===")


def main():
    """主函数"""
    print("腾讯云 DNSPod 客户端使用示例")
    print("================================")
    
    # 检查环境变量
    if not os.getenv('TENCENT_SECRET_ID') or not os.getenv('TENCENT_SECRET_KEY'):
        print("⚠️  请先设置环境变量:")
        print("   export TENCENT_SECRET_ID='your_secret_id'")
        print("   export TENCENT_SECRET_KEY='your_secret_key'")
        print("\n或者编辑 .env 文件")
        return
    
    try:
        # 1. 基础DNS操作
        basic_dns_operations()
        
        # 2. 批量操作
        batch_operations_example()
        
        # 3. 高级查询
        advanced_query_example()
        
        # 4. 动态IP更新（异步）
        asyncio.run(dynamic_ip_example())
        
        # 5. SSL证书管理
        ssl_cert_example()
        
    except KeyboardInterrupt:
        print("\n\n示例被用户中断")
    except Exception as e:
        print(f"\n\n示例执行失败: {e}")
    
    print("\n所有示例执行完成！")


if __name__ == "__main__":
    main()
