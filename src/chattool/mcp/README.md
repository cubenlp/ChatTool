# 阿里云DNS MCP服务

基于ChatTool项目和FastMCP框架构建的完整阿里云DNS管理服务，提供DNS记录管理、动态IP更新、SSL证书自动管理等功能。

## 功能特性

### 🔧 核心DNS管理功能（8个工具）

#### AliyunDNSClient 核心功能（6个）
- **list_domains** - 查看域名列表，支持分页参数
- **list_domain_records** - 查看域名解析记录，支持分页参数  
- **create_domain_record** - 添加域名解析记录，支持A/AAAA/CNAME/MX/TXT等记录类型
- **modify_domain_record** - 更新域名解析记录
- **remove_domain_record** - 删除域名解析记录
- **toggle_record_status** - 设置解析记录状态 (ENABLE/DISABLE)

#### 高级管理功能（2个）
- **update_dynamic_ip** - 动态IP监控和DNS自动更新功能
- **manage_ssl_certificates** - SSL证书自动更新和DNS挑战管理

### 🌍 多语言提示指导
- **中文版本** - 阿里云DNS管理指导，包含常见操作场景和最佳实践
- **英文版本** - Aliyun DNS Management Guide，涵盖配置和使用说明
- **日文版本** - Aliyun DNS管理ガイド，适合日文用户
- **故障排除** - 针对认证、网络、DNS记录等问题的排除指导
- **配置模板** - 针对网站、API、邮件等场景的DNS配置模板

### 📁 MCP资源管理
- **cert_directory_resource** - 读取证书目录结构和文件信息
- **cert_file_resource** - 读取特定证书文件内容
- **cert_list_resource** - 列出所有证书文件
- **system_environment_resource** - 系统环境信息和配置验证

## 安装和配置

### 环境要求

- Python 3.10+
- uv 包管理器
- openssl（证书功能需要）
- certbot（SSL证书自动更新需要）

### 安装步骤

1. **克隆ChatTool项目**（如果还没有）
```bash
git clone https://github.com/cubenlp/ChatTool.git
cd ChatTool/chattool/mcp/aliyun_dns_mcp
```

2. **安装uv包管理器**（如果还没有）
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **安装系统依赖**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openssl certbot

# CentOS/RHEL
sudo yum install openssl certbot

# macOS
brew install openssl certbot
```

4. **设置环境变量**
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID='your_access_key_id'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='your_access_key_secret'
```

### 阿里云API密钥获取

1. 登录[阿里云控制台](https://ram.console.aliyun.com/)
2. 前往访问控制(RAM) > 人员管理 > 用户
3. 创建新用户或选择现有用户
4. 为用户添加DNS管理权限：`AliyunDNSFullAccess`
5. 创建AccessKey，记录Access Key ID和Access Key Secret

## 使用方法

### 基本DNS操作

#### 查看域名列表
```python
# 查看所有域名
result = list_domains()

# 分页查询
result = list_domains(page_number=2, page_size=10)
```

#### 查看DNS记录
```python
# 查看指定域名的DNS记录
result = list_domain_records("example.com")

# 分页查询DNS记录
result = list_domain_records("example.com", page_number=1, page_size=20)
```

#### 创建DNS记录
```python
# 创建A记录
result = create_domain_record(
    domain_name="example.com",
    rr="www",
    record_type="A", 
    value="1.2.3.4",
    ttl=600
)

# 创建MX记录
result = create_domain_record(
    domain_name="example.com",
    rr="@",
    record_type="MX",
    value="mail.example.com",
    priority=10
)

# 创建TXT记录
result = create_domain_record(
    domain_name="example.com", 
    rr="@",
    record_type="TXT",
    value="v=spf1 include:_spf.example.com ~all"
)
```

#### 更新DNS记录
```python
# 更新现有记录
result = modify_domain_record(
    record_id="123456789",
    rr="www",
    record_type="A",
    value="2.3.4.5",
    ttl=300
)
```

#### 删除DNS记录
```python
# 删除指定记录
result = remove_domain_record(record_id="123456789")
```

#### 启用/禁用DNS记录
```python
# 禁用记录
result = toggle_record_status(record_id="123456789", status="DISABLE")

# 启用记录  
result = toggle_record_status(record_id="123456789", status="ENABLE")
```

### 动态IP管理

#### 单次检查和更新
```python
# 检查并更新动态IP
result = update_dynamic_ip(
    domain_name="example.com",
    rr="home",  # 子域名
    record_type="A",
    dns_ttl=300  # 动态IP建议使用较短TTL
)
```

### SSL证书管理

#### 自动申请和更新证书
```python
# 为单个域名申请证书
result = manage_ssl_certificates(
    domains=["example.com"],
    email="admin@example.com",
    staging=True  # 测试环境
)

# 为多个域名申请证书
result = manage_ssl_certificates(
    domains=["example.com", "www.example.com", "api.example.com"],
    email="admin@example.com",
    cert_dir="/etc/ssl/certs",
    private_key_dir="/etc/ssl/private",
    staging=False  # 生产环境
)
```

### 使用提示指导

#### 获取中文管理指导
```python
guide = aliyun_dns_guide_chinese("配置网站DNS解析")
```

#### 获取英文管理指导
```python
guide = aliyun_dns_guide_english("Setting up website DNS")
```

#### 获取故障排除指导
```python
# 认证问题排除
guide = dns_troubleshooting("authentication", "InvalidAccessKeyId.NotFound")

# DNS记录问题排除
guide = dns_troubleshooting("dns_record", "DomainRecordDuplicate")
```

#### 获取配置模板
```python
# 网站配置模板
template = dns_config_template("example.com", "website")

# API服务配置模板  
template = dns_config_template("api.example.com", "api")

# 邮件服务配置模板
template = dns_config_template("example.com", "email")
```

### 资源访问

#### 查看证书目录
```python
# 访问默认证书目录
cert://directory

# 访问指定目录
cert://directory
```

#### 读取证书文件
```python
# 读取特定证书文件
cert://file//etc/ssl/certs/example.com.crt
```

#### 列出所有证书
```python
# 获取系统中所有证书列表
cert://list
```

#### 查看系统环境
```python
# 获取环境配置和验证信息
system://environment
```

## 配置选项

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | ✅ | - | 阿里云Access Key ID |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | ✅ | - | 阿里云Access Key Secret |
| `ALIBABA_CLOUD_ENDPOINT` | ❌ | `alidns.cn-hangzhou.aliyuncs.com` | API端点 |
| `CERT_DIR` | ❌ | `/etc/ssl/certs` | 证书存储目录 |
| `PRIVATE_KEY_DIR` | ❌ | `/etc/ssl/private` | 私钥存储目录 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |

### DNS记录类型支持

| 记录类型 | 支持 | 说明 |
|----------|------|------|
| A | ✅ | IPv4地址记录 |
| AAAA | ✅ | IPv6地址记录 |
| CNAME | ✅ | 别名记录 |
| MX | ✅ | 邮件交换记录 |
| TXT | ✅ | 文本记录 |
| NS | ✅ | 域名服务器记录 |
| SRV | ✅ | 服务记录 |
| CAA | ✅ | 证书颁发机构授权记录 |

## 最佳实践

### 安全建议

1. **API密钥管理**
   - 使用最小权限原则，只授予DNS管理权限
   - 定期轮换API密钥
   - 不要在代码中硬编码密钥
   - 使用环境变量或密钥管理服务

2. **DNS记录管理**
   - 使用适当的TTL值（生产环境建议600-3600秒）
   - 为重要服务配置冗余记录
   - 定期审查和清理无用记录

3. **证书管理**
   - 使用生产环境前先在测试环境验证
   - 定期检查证书有效期
   - 备份重要证书文件

### 常见使用场景

#### 1. 网站部署DNS配置
```python
# 主域名A记录
create_domain_record("example.com", "@", "A", "1.2.3.4")

# www子域名CNAME
create_domain_record("example.com", "www", "CNAME", "example.com")

# 申请SSL证书
manage_ssl_certificates(
    domains=["example.com", "www.example.com"],
    email="admin@example.com"
)
```

#### 2. 动态IP环境配置
```python
# 创建动态DNS记录（较短TTL）
create_domain_record("example.com", "home", "A", "0.0.0.0", ttl=120)

# 定期更新IP地址
update_dynamic_ip("example.com", "home", dns_ttl=120)
```

#### 3. 邮件服务配置
```python
# MX记录
create_domain_record("example.com", "@", "MX", "mail.example.com", priority=10)

# 邮件服务器A记录  
create_domain_record("example.com", "mail", "A", "1.2.3.5")

# SPF记录
create_domain_record("example.com", "@", "TXT", "v=spf1 include:_spf.example.com ~all")
```

## 故障排除

### 常见问题

#### 1. 认证失败
```
错误: InvalidAccessKeyId.NotFound
```
**解决方案:**
- 检查Access Key ID是否正确
- 确认密钥是否已启用
- 验证用户权限设置

#### 2. DNS记录冲突
```
错误: DomainRecordDuplicate
```
**解决方案:**
- 先查询现有记录
- 删除重复记录或使用更新操作

#### 3. 证书申请失败
```
错误: DNS challenge failed
```
**解决方案:**
- 检查域名解析是否正确
- 确认DNS记录传播时间
- 验证Let's Encrypt服务状态

### 调试模式

设置详细日志输出：
```bash
export LOG_LEVEL=DEBUG
./run.sh
```

## 开发和测试

### 本地开发

1. 克隆项目
2. 设置开发环境变量
3. 运行测试

```bash
# 设置测试环境
export ALIBABA_CLOUD_ACCESS_KEY_ID='test_key'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='test_secret'
export LOG_LEVEL=DEBUG

# 运行测试
uv run pytest tests/
```

### 添加新功能

1. 在相应模块中添加函数
2. 在`server.py`中添加MCP工具装饰器
3. 更新文档和测试
4. 提交代码

## 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目基于MIT许可证开源。

## 联系方式

- 项目地址：[ChatTool](https://github.com/cubenlp/ChatTool)
- 问题反馈：请使用GitHub Issues

## 更新日志

### v1.0.0 (2025-01-12)
- 初始版本发布
- 支持8个核心DNS管理工具
- 多语言提示指导
- 证书目录资源管理
- 完整的错误处理和验证
