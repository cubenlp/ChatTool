
# DNS 管理工具文档

DNS 管理工具，支持腾讯云 DNSPod 与阿里云 DNS 两大云服务商。

## 安装及初始化

安装命令：

```bash
pip install "chattool[dev]"
```

代码导入：

```python
from chattool.tools.dns import create_dns_client, DNSClientType

# 创建客户端 - 支持字符串或枚举类型
client = create_dns_client('tencent')  # 或 DNSClientType.TENCENT
client = create_dns_client('aliyun')   # 或 DNSClientType.ALIYUN
```

工具模块：

- **`dynamic_ip_updater.py`** - 动态 IP 监控和自动 DNS 更新
- **`ssl_cert_updater.py`** - SSL 证书自动申请和更新（基于 Let's Encrypt）


## 配置认证

### 环境变量配置

**腾讯云 DNSPod：**
```bash
export TENCENT_SECRET_ID="你的SecretId"
export TENCENT_SECRET_KEY="你的SecretKey"
export TENCENT_REGION_ID="ap-guangzhou"  # 可选
```

**阿里云 DNS：**
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="你的AccessKeyId"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="你的AccessKeySecret"
export ALIBABA_CLOUD_REGION_ID="cn-hangzhou"  # 可选
```

### 配置文件

在 `CHATTOOL_CONFIG_DIR` 目录创建配置文件 `tencent.env` 和 `aliyun.env`，分别配置腾讯云 DNSPod 和阿里云 DNS 的认证信息。

不同系统的实际路径不同，可以通过以下代码查看，或者修改环境变量 `CHATTOOL_CONFIG_DIR` 来指定配置路径。

```python
from chattool.const import CHATTOOL_CONFIG_DIR

print(CHATTOOL_CONFIG_DIR) 
```

- Mac 系统下，默认路径为 `~/Library/Application Support/chattool/`。
- Windows 系统下，默认路径为 `%APPDATA%\chattool\`。
- Linux 系统下，默认路径为 `~/.config/chattool/`。

**腾讯云配置 (`tencent.env`)：**

```bash
TENCENT_SECRET_ID=你的SecretId
TENCENT_SECRET_KEY=你的SecretKey
```

**阿里云配置 (`aliyun.env`)：**

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=你的AccessKeyId
ALIBABA_CLOUD_ACCESS_KEY_SECRET=你的AccessKeySecret
```

## DNS 客户端 API

### 统一接口方法

两个云服务商的客户端都提供以下一致的方法：

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `describe_domains()` | 无 | `List[Dict]` | 获取域名列表 |
| `describe_domain_records(domain_name, subdomain=None, record_type=None)` | domain_name: str<br>subdomain: str (可选)<br>record_type: str (可选) | `List[Dict]` | 获取域名解析记录 |
| `describe_subdomain_records(sub_domain)` | sub_domain: str | `List[Dict]` | 获取子域名记录 |
| `add_domain_record(domain_name, rr, type_, value, ttl=600)` | domain_name: str<br>rr: str<br>type_: str<br>value: str<br>ttl: int | `str` (记录ID) | 添加解析记录 |
| `update_domain_record(record_id, rr, type_, value, ttl=600)` | record_id: str<br>rr: str<br>type_: str<br>value: str<br>ttl: int | `bool` | 更新解析记录 |
| `delete_domain_record(record_id)` | record_id: str | `bool` | 删除解析记录 |
| `set_domain_record_status(record_id, status)` | record_id: str<br>status: str | `bool` | 设置记录状态 |
| `set_record_value(domain_name, rr, type_, value, ttl=600)` | domain_name: str<br>rr: str<br>type_: str<br>value: str<br>ttl: int | `bool` | 智能设置（存在更新，不存在创建） |
| `delete_record_value(domain_name, rr, type_=None)` | domain_name: str<br>rr: str<br>type_: str (可选) | `bool` | 智能删除记录 |

### 基础使用示例

```python
from chattool.tools.dns import create_dns_client, DNSClientType
from chattool.const import CHATTOOL_CONFIG_DIR
from dotenv import load_dotenv

# 加载配置并创建客户端
load_dotenv(CHATTOOL_CONFIG_DIR / 'tencent.env')
client = create_dns_client(DNSClientType.TENCENT)

# 或者阿里云
# load_dotenv(CHATTOOL_CONFIG_DIR / 'aliyun.env')
# client = create_dns_client(DNSClientType.ALIYUN)

# 查看域名列表
domains = client.describe_domains()
print("域名列表:", domains)

# 查看解析记录
records = client.describe_domain_records("example.com")
for record in records:
    print(f"{record['RR']}.{record['DomainName']} -> {record['Value']} ({record['Type']})")

# 智能设置记录（推荐）
result = client.set_record_value(
    domain_name="example.com",
    rr="www",
    type_="A",
    value="1.2.3.4",
    ttl=600
)
print("设置结果:", result)
```

## SSL 证书自动管理

### 功能特性

- 基于 Let's Encrypt 的 DNS-01 挑战验证
- 自动管理 DNS TXT 记录
- 支持多域名和通配符证书
- 证书文件自动复制到指定目录
- nginx 配置自动重载

### 命令行使用

```bash
# 申请新证书（生产环境）
chattool.ssl_cert_updater \
  -d example.com \
  -d www.example.com \
  -e admin@example.com \
  --cert-dir /etc/ssl/certs \
  --private-key-dir /etc/ssl/private
```
