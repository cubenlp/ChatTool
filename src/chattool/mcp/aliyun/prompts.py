#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP提示模板

提供多语言的阿里云DNS管理指导和最佳实践。
"""

def chinese_dns_management_guide(context: str) -> str:
    """
    中文版阿里云DNS管理指导
    
    Args:
        context: 上下文信息
        
    Returns:
        中文版DNS管理指导
    """
    return f"""# 阿里云DNS管理指导

## 上下文
{context}

## 常见DNS操作场景

### 1. 基础域名解析配置
- **A记录**: 将域名指向IPv4地址
- **AAAA记录**: 将域名指向IPv6地址
- **CNAME记录**: 将域名指向另一个域名
- **MX记录**: 配置邮件服务器
- **TXT记录**: 添加文本信息，常用于验证

### 2. DNS记录管理最佳实践
- 使用适当的TTL值（通常300-3600秒）
- 为重要服务配置冗余记录
- 定期检查和清理无用记录
- 使用有意义的主机记录名称

### 3. 动态IP环境配置
- 配置动态IP更新服务
- 设置较短的TTL值（120-300秒）
- 监控IP变化和更新状态

### 4. SSL证书自动化管理
- 使用Let's Encrypt免费证书
- 配置DNS-01挑战验证
- 设置自动更新机制

## 安全建议
- 妥善保管API密钥
- 使用最小权限原则
- 定期轮换访问密钥
- 监控DNS修改日志

## 故障排除
1. 检查DNS记录配置
2. 验证TTL设置
3. 确认API权限
4. 查看操作日志"""


def english_dns_management_guide(context: str) -> str:
    """
    English version Aliyun DNS Management Guide
    
    Args:
        context: Context information
        
    Returns:
        English DNS management guide
    """
    return f"""# Aliyun DNS Management Guide

## Context
{context}

## Common DNS Operation Scenarios

### 1. Basic Domain Resolution Configuration
- **A Record**: Point domain to IPv4 address
- **AAAA Record**: Point domain to IPv6 address  
- **CNAME Record**: Point domain to another domain
- **MX Record**: Configure mail server
- **TXT Record**: Add text information, commonly used for verification

### 2. DNS Record Management Best Practices
- Use appropriate TTL values (typically 300-3600 seconds)
- Configure redundant records for important services
- Regularly check and clean unused records
- Use meaningful host record names

### 3. Dynamic IP Environment Configuration
- Configure dynamic IP update services
- Set shorter TTL values (120-300 seconds)
- Monitor IP changes and update status

### 4. SSL Certificate Automation Management
- Use Let's Encrypt free certificates
- Configure DNS-01 challenge verification
- Set up automatic renewal mechanisms

## Security Recommendations
- Securely store API keys
- Use principle of least privilege
- Regularly rotate access keys
- Monitor DNS modification logs

## Troubleshooting
1. Check DNS record configuration
2. Verify TTL settings
3. Confirm API permissions
4. Review operation logs"""


def japanese_dns_management_guide(context: str) -> str:
    """
    日本語版Aliyun DNS管理ガイド
    
    Args:
        context: コンテキスト情報
        
    Returns:
        日本語版DNS管理ガイド
    """
    return f"""# Aliyun DNS管理ガイド

## コンテキスト
{context}

## 一般的なDNS操作シナリオ

### 1. 基本ドメイン解決設定
- **Aレコード**: ドメインをIPv4アドレスに向ける
- **AAAAレコード**: ドメインをIPv6アドレスに向ける
- **CNAMEレコード**: ドメインを別のドメインに向ける
- **MXレコード**: メールサーバーを設定
- **TXTレコード**: テキスト情報を追加、検証によく使用

### 2. DNSレコード管理のベストプラクティス
- 適切なTTL値を使用（通常300-3600秒）
- 重要なサービスの冗長レコードを設定
- 定期的に未使用レコードをチェック・クリーンアップ
- 意味のあるホストレコード名を使用

### 3. 動的IP環境設定
- 動的IP更新サービスを設定
- 短いTTL値を設定（120-300秒）
- IP変更と更新状況を監視

### 4. SSL証明書自動管理
- Let's Encrypt無料証明書を使用
- DNS-01チャレンジ検証を設定
- 自動更新メカニズムを設定

## セキュリティ推奨事項
- APIキーを安全に保存
- 最小権限の原則を使用
- 定期的にアクセスキーをローテーション
- DNS変更ログを監視

## トラブルシューティング
1. DNSレコード設定を確認
2. TTL設定を検証
3. API権限を確認
4. 操作ログを確認"""


def dns_troubleshooting_guide(issue_type: str, error_message: str = "") -> str:
    """
    DNS故障排除指导
    
    Args:
        issue_type: 问题类型
        error_message: 错误信息
        
    Returns:
        故障排除指导
    """
    guides = {
        "authentication": f"""
# 认证问题排除

## 错误信息
{error_message}

## 检查步骤
1. 验证环境变量是否正确设置：
   - ALIBABA_CLOUD_ACCESS_KEY_ID
   - ALIBABA_CLOUD_ACCESS_KEY_SECRET

2. 确认API密钥权限：
   - 登录阿里云控制台
   - 检查RAM用户权限
   - 确认DNS服务授权

3. 网络连接检查：
   - 测试网络连通性
   - 检查防火墙设置
   - 验证代理配置
        """,
        
        "dns_record": f"""
# DNS记录操作问题排除

## 错误信息
{error_message}

## 检查步骤
1. 验证域名配置：
   - 确认域名在阿里云DNS管理
   - 检查域名状态
   - 验证NS记录

2. 记录参数检查：
   - 验证记录类型和值格式
   - 检查TTL值范围
   - 确认解析线路设置

3. API限制检查：
   - 确认API调用频率限制
   - 检查账户余额
   - 验证服务状态
        """,
        
        "network": f"""
# 网络连接问题排除

## 错误信息
{error_message}

## 检查步骤
1. 网络连通性：
   - ping alidns.cn-hangzhou.aliyuncs.com
   - 检查DNS解析
   - 测试HTTP/HTTPS连接

2. 代理和防火墙：
   - 检查代理设置
   - 验证防火墙规则
   - 确认端口开放

3. 系统配置：
   - 检查系统时间
   - 验证证书设置
   - 确认网络配置
        """
    }
    
    return guides.get(issue_type, f"未知问题类型: {issue_type}\n错误信息: {error_message}")


def dns_configuration_template(domain_name: str, use_case: str) -> str:
    """
    DNS配置模板生成器
    
    Args:
        domain_name: 域名
        use_case: 使用场景
        
    Returns:
        DNS配置模板
    """
    templates = {
        "website": f"""
# 网站DNS配置模板 - {domain_name}

## 基础解析配置
- @ A 1.2.3.4 (主域名指向服务器IP)
- www CNAME @ (www子域名指向主域名)
- * A 1.2.3.4 (泛解析，可选)

## 邮件服务配置（可选）
- @ MX 10 mail.{domain_name}
- mail A 1.2.3.5
- @ TXT "v=spf1 include:_spf.{domain_name} ~all"

## SSL证书验证（临时）
- _acme-challenge TXT "验证字符串"

## TTL建议
- 主要记录：600秒
- 临时记录：120秒
        """,
        
        "api": f"""
# API服务DNS配置模板 - {domain_name}

## API服务配置
- api A 1.2.3.4 (API服务器IP)
- api-v2 A 1.2.3.5 (API v2服务器IP)
- cdn CNAME api.cdn-provider.com (CDN加速)

## 负载均衡配置
- api A 1.2.3.4
- api A 1.2.3.5 (多IP负载均衡)

## 监控和健康检查
- health A 1.2.3.6
- status CNAME health.{domain_name}

## TTL建议
- 生产环境：300-600秒
- 测试环境：120秒
        """,
        
        "email": f"""
# 邮件服务DNS配置模板 - {domain_name}

## MX记录配置
- @ MX 10 mail.{domain_name}
- @ MX 20 backup-mail.{domain_name}

## 邮件服务器A记录
- mail A 1.2.3.4
- backup-mail A 1.2.3.5

## SPF记录
- @ TXT "v=spf1 include:_spf.{domain_name} ~all"

## DKIM记录（示例）
- selector._domainkey TXT "v=DKIM1; k=rsa; p=公钥..."

## DMARC记录
- _dmarc TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain_name}"

## TTL建议
- MX记录：3600秒
- 其他记录：600秒
        """
    }
    
    return templates.get(use_case, f"# 通用DNS配置模板 - {domain_name}\n\n请选择具体的使用场景以获取详细配置。")
