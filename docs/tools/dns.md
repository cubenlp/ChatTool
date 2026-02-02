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

ChatTool 提供了统一的 DNS 管理 CLI 工具，用于快速查看、更新 DNS 记录（常用于 DDNS 场景）以及管理 SSL 证书。

### 基本用法

#### 1. 查看/管理 DNS 记录

```bash
# 获取 DNS 记录 (get)
# 完整域名方式:
chattool dns get test.example.com
# 分开指定方式:
chattool dns get -d example.com -r test

# 设置 DNS 记录 (set) - 自动处理新增或更新
# 将 test.example.com 解析到 1.2.3.4
chattool dns set test.example.com -v 1.2.3.4
# 指定类型和 TTL
chattool dns set test.example.com -v "some-text-value" -t TXT --ttl 300
```

#### 2. 动态域名更新 (DDNS)

```bash
# 1. 公网 IP 更新 (默认)
# 自动获取当前公网 IP 并更新到 'home.example.com'
# 简化写法：
chattool dns ddns home.example.com
# 或传统写法：
chattool dns ddns -d example.com -r home

# 2. 局域网 IP 更新 (自动探测)
# 自动探测局域网 IP (192.168.x.x, 10.x.x.x 等) 并更新
chattool dns ddns nas.example.com --ip-type local

# 3. 局域网 IP 更新 (指定网段过滤)
# 当存在多个局域网 IP 时，可指定网段进行筛选 (如仅匹配 192.168.1.x)
chattool dns ddns nas.example.com --ip-type local --local-ip-cidr 192.168.1.0/24

# 4. 持续监控模式 (后台运行，IP 变动时自动更新)
chattool dns ddns home.example.com --monitor
```

**参数说明**：
- `[DOMAIN]`: (可选位置参数) 完整域名，如 `home.example.com`。如果提供此参数，则忽略 `-d` 和 `-r`。
- `--domain, -d`: (可选) 域名名称，如 `example.com`
- `--rr, -r`: (可选) 主机记录，如 `www`, `@`, `home`
- `--interval, -i`: (可选) 监控间隔秒数 (默认 120s)
- `--ip-type`: (可选) IP 类型，`public` (默认) 或 `local`
- `--local-ip-cidr`: (可选) 局域网 IP 过滤网段，仅当 `ip-type=local` 时有效 (如 `192.168.1.0/24`)

#### 3. SSL 证书自动更新

ChatTool 内置了轻量级 ACME v2 客户端，支持通过 DNS-01 挑战自动申请和更新 Let's Encrypt 证书。

> **注意**：
> 1. 无需安装 `certbot` 或 `acme.sh`。
> 2. 不需要 root 权限 (证书默认保存在用户目录或指定位置)。
> 3. 必须配置 DNS 凭证 (因为需要添加 TXT 记录进行验证)。

```bash
# 申请证书 (自动处理 DNS 验证)
chattool dns cert-update -d *.example.com -d example.com -e admin@example.com

# 指定证书保存目录
chattool dns cert-update -d *.example.com -e admin@example.com --cert-dir ./certs
```

**参数说明**：
- `--domains, -d`: (必填) 域名列表，支持多次指定。支持泛域名 (如 `*.example.com`)。
- `--email, -e`: (必填) Let's Encrypt 账户邮箱 (用于接收通知)。
- `--cert-dir`: (可选) 证书存储根目录 (默认: `certs`)。证书将保存在 `<cert-dir>/<domain>/` 下。
- `--staging`: (可选) 使用 Let's Encrypt 测试环境 (建议首次测试时使用)。

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
