# 腾讯云 DNSPod 客户端

基于腾讯云官方 SDK 实现的 DNSPod 域名解析记录管理客户端，提供完整的 CRUD 操作功能，以及动态IP更新和SSL证书自动更新等高级功能。

## 安装依赖

```bash
# 安装腾讯云SDK
pip install tencentcloud-sdk-python

# 安装其他依赖（动态IP更新需要）
pip install aiohttp click colorama

# SSL证书功能需要额外安装
pip install dnspython  # DNS记录验证
```

## 快速开始

### 1. 获取腾讯云 API 密钥

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 进入 [访问管理 → API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 创建密钥，获取 `SecretId` 和 `SecretKey`

### 2. 配置认证信息

复制并编辑环境变量配置文件：

```bash
cp .env.example .env
# 编辑 .env 文件，填入您的密钥信息
```

或者设置环境变量：

```bash
export TENCENT_SECRET_ID="your_secret_id"
export TENCENT_SECRET_KEY="your_secret_key"
```

### 3. 基本使用

```python
from chattool.tools import TencentDNSClient

# 初始化客户端
client = TencentDNSClient()

# 查看域名列表
domains = client.describe_domains()
for domain in domains:
    print(f"{domain['DomainName']} (ID: {domain['DomainId']})")

# 查看解析记录
records = client.describe_domain_records("example.com")
for record in records:
    print(f"{record['RR']}.example.com {record['Type']} {record['Value']}")

# 创建解析记录
record_id = client.add_domain_record(
    domain_name="example.com",
    rr="www",
    type_="A",
    value="1.2.3.4",
    ttl=600
)

# 智能设置记录值（不存在则创建，存在则更新）
success = client.set_record_value(
    domain_name="example.com",
    rr="api",
    type_="A", 
    value="10.0.0.1",
    ttl=300
)
```

## 高级功能

### 动态IP更新

自动监控公网IP变化并更新DNS记录：

```bash
# 持续监控模式
python -m chattool.tools.tencent_dns.dynamic_ip_updater monitor \
    --domain example.com \
    --rr www \
    --interval 120

# 执行一次更新
python -m chattool.tools.tencent_dns.dynamic_ip_updater update \
    --domain example.com \
    --rr www

# 列出DNS记录
python -m chattool.tools.tencent_dns.dynamic_ip_updater list-records \
    --domain example.com
```

### SSL证书自动管理

基于Let's Encrypt和DNS-01挑战的SSL证书自动申请和续期：

```bash
# 申请新证书
python -m chattool.tools.tencent_dns.ssl_cert_updater issue \
    -d example.com \
    -d www.example.com \
    -e your@email.com

# 续期证书
python -m chattool.tools.tencent_dns.ssl_cert_updater renew \
    -d example.com \
    -e your@email.com

# 自动检查并更新
python -m chattool.tools.tencent_dns.ssl_cert_updater auto-update \
    -d example.com \
    -d www.example.com \
    -e your@email.com

# 检查证书状态
python -m chattool.tools.tencent_dns.ssl_cert_updater check \
    -d example.com \
    -e your@email.com
```

## API 参考

### TencentDNSClient

主要的DNS客户端类，提供所有DNS管理功能。

#### 初始化

```python
TencentDNSClient(
    secret_id: Optional[str] = None,
    secret_key: Optional[str] = None,
    region: str = "ap-guangzhou",
    endpoint: Optional[str] = None,
    logger: Optional[logging.Logger] = None
)
```

#### 主要方法

- `describe_domains()` - 查询域名列表
- `describe_domain_records()` - 查询解析记录
- `describe_subdomain_records()` - 查询子域名记录
- `add_domain_record()` - 添加解析记录
- `update_domain_record()` - 修改解析记录
- `delete_domain_record()` - 删除解析记录
- `set_domain_record_status()` - 设置记录状态
- `set_record_value()` - 智能设置记录值
- `delete_record_value()` - 删除指定记录

### DynamicIPUpdater

动态IP监控和DNS更新器。

```python
DynamicIPUpdater(
    domain_name: str,
    rr: str,
    record_type: str = "A",
    dns_ttl: int = 600,
    max_retries: int = 3,
    retry_delay: int = 5,
    logger=None
)
```

### SSLCertUpdater

SSL证书自动更新器。

```python
SSLCertUpdater(
    domains: List[str],
    email: str,
    cert_dir: str = "/etc/ssl/certs",
    private_key_dir: str = "/etc/ssl/private",
    staging: bool = False,
    logger=None
)
```

## 支持的记录类型

- **A**: IPv4 地址记录
- **AAAA**: IPv6 地址记录
- **CNAME**: 别名记录
- **MX**: 邮件交换记录
- **TXT**: 文本记录
- **NS**: 域名服务器记录
- **SRV**: 服务记录
- **CAA**: 证书颁发机构授权记录
- **HTTPS**: HTTPS 记录
- **SVCB**: 服务绑定记录

## 常见线路类型

- **默认**: 默认线路
- **境内**: 中国境内
- **境外**: 中国境外
- **电信**: 中国电信
- **联通**: 中国联通
- **移动**: 中国移动
- **教育网**: 中国教育和科研计算机网

## 错误处理

客户端使用腾讯云官方SDK的异常处理机制：

```python
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

try:
    records = client.describe_domain_records("example.com")
except TencentCloudSDKException as e:
    print(f"API调用失败: {e}")
```

常见错误码：

- `AuthFailure`: 认证失败
- `InvalidParameter.DomainInvalid`: 域名无效
- `InvalidParameter.RecordTypeInvalid`: 记录类型无效
- `RequestLimitExceeded`: 请求频率超限

## 配置文件说明

### .env 环境变量

```bash
# 必需配置
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key

# 可选配置
TENCENT_REGION=ap-guangzhou
DOMAIN_NAME=example.com
RR=www
RECORD_TYPE=A
DNS_TTL=600

# 监控配置
IP_CHECK_INTERVAL=120
IP_CHECK_TIMEOUT=10
MAX_RETRIES=3
RETRY_DELAY=5

# 日志配置
LOG_FILE=dynamic_ip_updater.log
LOG_LEVEL=INFO
```
