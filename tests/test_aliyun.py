import logging
import pytest
import os
from chattool.tools.dns import create_dns_client
from chattool.utils import setup_logger

# 只有当 ALIBABA_CLOUD_ACCESS_KEY_ID 环境变量存在时才运行测试
@pytest.mark.skipif(not os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'), reason="Missing Aliyun credentials")
def test_aliyun_dns():
    logger = setup_logger('test_aliyun', log_level='INFO')
    client = create_dns_client('aliyun', logger=logger)
    
    domain = 'qpetlover.cn'
    rr = 'test-api-refactor'
    
    print(f"=== 测试阿里云 DNS: {domain} ===")
    
    # 1. 列出域名
    print("\n1. 获取域名列表...")
    domains = client.describe_domains()
    assert domains is not None
    # 只要不报错即可，域名列表可能为空
    
    # 2. 添加记录
    print(f"\n2. 添加记录 {rr}.{domain}...")
    # 先清理可能存在的记录
    client.delete_subdomain_records(domain, rr, type_='A')
    
    record_id = client.add_domain_record(domain, rr, 'A', '1.2.3.4')
    assert record_id is not None
    print(f" -> 成功，RecordId: {record_id}")

    # 3. 查询记录
    print(f"\n3. 查询记录 {rr}.{domain}...")
    records = client.describe_subdomain_records(domain, rr)
    assert len(records) > 0
    found = False
    for r in records:
        if r['RecordId'] == record_id:
            assert r['Value'] == '1.2.3.4'
            found = True
            break
    assert found
        
    # 4. 更新记录
    print(f"\n4. 更新记录 {record_id}...")
    success = client.update_domain_record(record_id, rr, 'A', '5.6.7.8')
    assert success
    print(f" -> 成功")
    
    # 验证更新
    records = client.describe_subdomain_records(domain, rr)
    found = False
    for r in records:
        if r['RecordId'] == record_id:
            assert r['Value'] == '5.6.7.8'
            found = True
            break
    assert found

    # 5. 删除记录
    print(f"\n5. 删除记录 {record_id}...")
    success = client.delete_domain_record(record_id)
    assert success
    print(f" -> 成功")
    
    # 验证删除
    records = client.describe_subdomain_records(domain, rr)
    # 确保刚才的记录ID不存在了
    for r in records:
        assert r['RecordId'] != record_id
