# DNS 工具箱文档

ChatTool 提供了一套统一的 DNS 管理工具，旨在简化跨云厂商（目前支持阿里云和腾讯云）的域名解析记录管理。

## 核心特性

- **统一接口**：无论底层是阿里云还是腾讯云，都使用相同的 API 进行操作。
- **自动配置**：集成 ChatTool 的统一配置系统，支持从 `.env` 文件自动读取凭证。
- **命令行工具**：提供开箱即用的 DDNS 更新 CLI 工具。
- **异步支持**：提供异步获取公网 IP 的辅助方法。

## 快速开始

### 1. 配置凭证

在项目根目录或配置目录下的 `.env` 文件中设置相应的凭证：

```bash
# 阿里云配置
ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
ALIBABA_CLOUD_REGION_ID="cn-hangzhou"

# 腾讯云配置
TENCENT_SECRET_ID="your-secret-id"
TENCENT_SECRET_KEY="your-secret-key"
TENCENT_REGION_ID="ap-guangzhou"
```

### 2. Python API 使用

```python
from chattool.tools.dns import create_dns_client

# 工厂方法创建客户端
# provider 可选: 'aliyun', 'tencent'
client = create_dns_client("aliyun")

# 1. 获取域名列表
domains = client.describe_domains()
for domain in domains:
    print(f"域名: {domain['DomainName']}, ID: {domain['DomainId']}")

# 2. 添加解析记录
record_id = client.add_domain_record(
    domain_name="example.com",
    rr="www",           # 主机记录
    type_="A",          # 记录类型
    value="1.1.1.1",    # 记录值
    ttl=600             # TTL
)

# 3. 查询解析记录
records = client.describe_domain_records("example.com")
for r in records:
    print(f"{r['RR']} -> {r['Value']}")

# 4. 幂等更新（如果记录存在则更新，不存在则创建）
client.set_record_value(
    domain_name="example.com",
    rr="api",
    type_="A",
    value="2.2.2.2"
)

# 5. 删除子域名的所有记录
client.delete_subdomain_records("example.com", "temp")
```

## 命令行工具 (CLI)

ChatTool 提供了 `aliyun-dns-updater` 命令，用于快速更新 DNS 记录（常用于 DDNS 场景）。

### 基本用法

```bash
chattool.aliyun-dns-updater --domain example.com --rr home --type A
```

该命令会自动获取当前机器的公网 IP，并更新到 `home.example.com` 的 A 记录中。

### 参数说明

- `--domain`: (必填) 域名名称，如 `example.com`
- `--rr`: (必填) 主机记录，如 `www`, `@`, `home`
- `--type`: (必填) 记录类型，支持 `A` (IPv4) 或 `AAAA` (IPv6)
- `--value`: (可选) 显式指定 IP 地址。如果不填，则自动获取当前公网 IP。

### 示例

**使用当前公网 IP 更新**
```bash
chattool.aliyun-dns-updater --domain mysite.com --rr vpn --type A
```

**指定 IP 更新**
```bash
chattool.aliyun-dns-updater --domain mysite.com --rr static --type A --value 192.168.1.100
```

## 扩展指南

如果需要支持新的云厂商，只需继承 `DNSClient` 基类并实现以下抽象方法：

```python
from chattool.tools.dns.base import DNSClient

class MyCloudDNSClient(DNSClient):
    def describe_domains(self, ...): ...
    def describe_domain_records(self, ...): ...
    def add_domain_record(self, ...): ...
    def update_domain_record(self, ...): ...
    def delete_domain_record(self, ...): ...
```
