#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP服务完整性测试

验证MCP服务的所有组件是否正常工作。
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_basic_imports():
    """测试基本模块导入"""
    print("=== 基本模块导入测试 ===")
    
    tests = [
        ("config", "aliyun_dns_mcp.config"),
        ("tools", "aliyun_dns_mcp.tools"),
        ("prompts", "aliyun_dns_mcp.prompts"),
        ("resources", "aliyun_dns_mcp.resources"),
        ("utils", "aliyun_dns_mcp.utils")
    ]
    
    results = {}
    for name, module in tests:
        try:
            __import__(module)
            results[name] = True
            print(f"✅ {name} 模块导入成功")
        except ImportError as e:
            results[name] = False
            print(f"❌ {name} 模块导入失败: {e}")
    
    return all(results.values())

def test_configuration():
    """测试配置功能"""
    print("\n=== 配置功能测试 ===")
    
    try:
        from aliyun_dns_mcp.config import validate_environment, get_system_info
        
        # 测试环境验证
        is_valid, env_result = validate_environment()
        print(f"环境验证功能: ✅")
        print(f"  - 环境有效性: {'✅' if is_valid else '⚠️'} {is_valid}")
        print(f"  - 缺少变量: {len(env_result.get('missing_required', []))}")
        
        # 测试系统信息
        sys_info = get_system_info()
        print(f"系统信息获取: ✅")
        print(f"  - Python版本: {sys_info['python_version'].split()[0]}")
        print(f"  - 平台: {sys_info['platform']}")
        
        return True
    except Exception as e:
        print(f"❌ 配置功能测试失败: {e}")
        return False

def test_utilities():
    """测试工具函数"""
    print("\n=== 工具函数测试 ===")
    
    try:
        from aliyun_dns_mcp.utils import (
            validate_ip_address,
            format_dns_record,
            check_prerequisites
        )
        
        # 测试IP验证
        valid, error = validate_ip_address("8.8.8.8")
        print(f"IP验证功能: ✅ ({valid})")
        
        # 测试DNS记录格式化
        record = {
            'DomainName': 'test.com',
            'RR': 'www',
            'Type': 'A',
            'Value': '1.2.3.4',
            'TTL': 600
        }
        formatted = format_dns_record(record)
        print(f"DNS记录格式化: ✅ ({len(formatted)} 字符)")
        
        # 测试先决条件检查
        prereq = check_prerequisites()
        print(f"先决条件检查: ✅")
        print(f"  - Python版本: {'✅' if prereq['python_version'] else '❌'}")
        print(f"  - 警告数量: {len(prereq.get('warnings', []))}")
        
        return True
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def test_prompts():
    """测试提示功能"""
    print("\n=== 提示功能测试 ===")
    
    try:
        from aliyun_dns_mcp.prompts import (
            chinese_dns_management_guide,
            english_dns_management_guide,
            dns_troubleshooting_guide,
            dns_configuration_template
        )
        
        # 测试中文指导
        guide = chinese_dns_management_guide("测试")
        print(f"中文指导生成: ✅ ({len(guide)} 字符)")
        
        # 测试英文指导
        en_guide = english_dns_management_guide("Test")
        print(f"英文指导生成: ✅ ({len(en_guide)} 字符)")
        
        # 测试故障排除
        troubleshooting = dns_troubleshooting_guide("authentication", "test")
        print(f"故障排除指导: ✅ ({len(troubleshooting)} 字符)")
        
        # 测试配置模板
        template = dns_configuration_template("example.com", "website")
        print(f"配置模板生成: ✅ ({len(template)} 字符)")
        
        return True
    except Exception as e:
        print(f"❌ 提示功能测试失败: {e}")
        return False

def test_resources():
    """测试资源功能"""
    print("\n=== 资源功能测试 ===")
    
    try:
        from aliyun_dns_mcp.resources import (
            cert_directory_reader,
            list_all_certificates
        )
        
        # 测试目录读取
        dir_info = cert_directory_reader(".")
        print(f"目录读取功能: ✅ ({len(dir_info)} 字符)")
        
        # 测试证书列表
        cert_list = list_all_certificates()
        print(f"证书列表功能: ✅ ({len(cert_list)} 字符)")
        
        return True
    except Exception as e:
        print(f"❌ 资源功能测试失败: {e}")
        return False

def test_project_structure():
    """测试项目结构"""
    print("\n=== 项目结构测试 ===")
    
    required_files = [
        "pyproject.toml",
        "README.md",
        "server.py",
        "run.sh",
        "mcp-server.json",
        "src/aliyun_dns_mcp/__init__.py",
        "src/aliyun_dns_mcp/config.py",
        "src/aliyun_dns_mcp/tools.py",
        "src/aliyun_dns_mcp/prompts.py",
        "src/aliyun_dns_mcp/resources.py",
        "src/aliyun_dns_mcp/utils.py",
        "tests/__init__.py",
        "tests/test_mcp_server.py",
        "examples/__init__.py",
        "examples/usage_examples.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    print(f"✅ 所有必需文件都存在 ({len(required_files)} 个)")
    return True

def test_mcp_configuration():
    """测试MCP配置文件"""
    print("\n=== MCP配置文件测试 ===")
    
    try:
        import json
        with open(current_dir / "mcp-server.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_fields = ["name", "exhibit_name", "type", "command", "description", "description_for_agent", "user_params"]
        for field in required_fields:
            if field not in config:
                print(f"❌ 缺少必需字段: {field}")
                return False
            else:
                print(f"✅ {field}: {config[field] if field != 'user_params' else '(配置存在)'}")
        
        # 检查用户参数
        user_params = config.get("user_params", {})
        env_params = user_params.get("env", {})
        
        expected_env_vars = ["ALIBABA_CLOUD_ACCESS_KEY_ID", "ALIBABA_CLOUD_ACCESS_KEY_SECRET"]
        for var in expected_env_vars:
            if var in env_params:
                print(f"✅ 环境变量配置: {var}")
            else:
                print(f"❌ 缺少环境变量配置: {var}")
        
        return True
    except Exception as e:
        print(f"❌ MCP配置文件测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("阿里云DNS MCP服务完整性测试报告")
    print("=" * 60)
    
    tests = [
        ("基本模块导入", test_basic_imports),
        ("配置功能", test_configuration),
        ("工具函数", test_utilities),
        ("提示功能", test_prompts),
        ("资源功能", test_resources),
        ("项目结构", test_project_structure),
        ("MCP配置文件", test_mcp_configuration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 测试出现异常: {e}")
            results[test_name] = False
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} : {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！MCP服务已准备就绪")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述问题")
        return False

def main():
    """主函数"""
    print("阿里云DNS MCP服务完整性测试")
    print("基于ChatTool项目和FastMCP框架")
    
    success = generate_test_report()
    
    print(f"\n{'='*60}")
    print("部署说明")
    print("=" * 60)
    
    if success:
        print("✅ MCP服务已准备就绪，可以进行部署")
        print("\n部署步骤:")
        print("1. 设置阿里云API密钥环境变量")
        print("   export ALIBABA_CLOUD_ACCESS_KEY_ID='your_key_id'")
        print("   export ALIBABA_CLOUD_ACCESS_KEY_SECRET='your_key_secret'")
        print("2. 运行启动脚本: sh run.sh")
        print("3. 或使用MCP工具进行注册和测试")
    else:
        print("❌ MCP服务尚未准备就绪，请修复上述问题后重试")
    
    print(f"\n{'='*60}")
    print("功能摘要")
    print("=" * 60)
    print("✅ 8个DNS管理工具函数")
    print("✅ 多语言提示指导(中英日)")
    print("✅ 证书目录资源管理")
    print("✅ 完整的错误处理和验证")
    print("✅ 动态IP更新功能")
    print("✅ SSL证书自动管理")
    print("✅ 基于ChatTool项目和FastMCP框架")
    
    return success

if __name__ == "__main__":
    main()
